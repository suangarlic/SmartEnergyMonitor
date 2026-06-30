# services/behavior_service.py - 行为分析轮询服务
# 每 30s 从数据库取最近 6 条数据，运行 BehaviorComparator，
# 生成标准化 llm_input，存储结果供前端/大模型调用

import json
import sys
import threading
import time
import pandas as pd

from analyzer.behavior_compare import BehaviorComparator


def _get_control_switch():
    """读取 app.py 中的全局开关状态"""
    main_mod = sys.modules.get('__main__')
    if main_mod and hasattr(main_mod, 'auto_control_enabled'):
        return main_mod.auto_control_enabled
    return False  # 默认关闭，安全兜底


class BehaviorAnalysisService:
    """行为分析轮询服务，定时从数据库拉取最新数据并执行比对"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._comparator = BehaviorComparator(
            debounce_count=3,  # 增加防抖次数，减少误触发
        )
        # 记录上次执行的命令，用于判断档位是否变化
        self._last_fan_level = -1
        self._last_light_level = -1
        self._latest_result: dict | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()  # 用于立即中断 sleep

        # 存储最新控制结果，供前端 AI 状态卡片查询
        self._control_status = {
            "reason": "系统正在分析环境数据...",
            "action": "无动作",
            "executed": False,
            "time": "",
            "scenario": "normal",
        }

    # ----------------------------------------------------------
    # 核心分析
    # ----------------------------------------------------------
    def analyze_once(self) -> dict | None:
        """
        从数据库取最近 6 条数据，执行比对，返回 llm_input。

        Returns:
            llm_input dict 或 None（数据不足）
        """
        # 闸门判断：开关关闭时直接跳过，不执行分析、不下发控制指令
        if not _get_control_switch():
            print(f"[Behavior] [自动控制已关闭] 跳过本轮分析")
            return None

        from data.sensor_repository import get_latest_records

        rows = get_latest_records(6)
        if len(rows) < 6:
            print(f"[Behavior] 数据不足 ({len(rows)}/6)，跳过本轮")
            return None

        window_df = pd.DataFrame(rows)
        compare_result = self._comparator.compare(window_df)
        if compare_result is None:
            return None

        llm_input = self._comparator.build_llm_input(window_df, compare_result)
        llm_input["scenario"] = compare_result.scenario
        llm_input["trigger"] = compare_result.trigger
        llm_input["action"] = compare_result.action

        self._latest_result = llm_input

        print(f"[Behavior] [自动控制={_get_control_switch()}] {llm_input['time']} | {compare_result.scenario} | "
              f"trigger={compare_result.trigger}")
        if compare_result.trigger:
            print(f"  → {compare_result.reason}")

        # 检查档位是否发生变化
        target_fan = llm_input.get("baseline_status", {}).get("fan", 0)
        target_light = llm_input.get("baseline_status", {}).get("light", 0)
        has_level_change = (target_fan != self._last_fan_level) or (target_light != self._last_light_level)

        # 调用大模型生成解释，保存到 reason.txt
        # 优化：只有在场景触发且档位发生变化时才调用 API，大幅减少调用频率
        reason = ""
        if compare_result.trigger and has_level_change and _get_control_switch():
            try:
                from AI_API import AIAnalyzer
                reason = AIAnalyzer().explain_behavior(llm_input)
                with open("reason.txt", "w", encoding="utf-8") as f:
                    f.write(reason)
                print(f"  [LLM] {reason}")
                # 更新记录的档位
                self._last_fan_level = target_fan
                self._last_light_level = target_light
            except Exception as e:
                reason = "AI分析中..."
                print(f"  [LLM] 调用失败: {e}")
        elif compare_result.trigger and not has_level_change:
            print(f"  [LLM] 跳过调用：档位未变化 (fan={target_fan}, light={target_light})")
        elif not _get_control_switch():
            print(f"  [LLM] 跳过调用：自动控制开关已关闭")

        # 自动控制：仅对 energy_saving / comfort_adjust 场景下发设备指令
        self._apply_control(llm_input, reason)

        return llm_input

    # ----------------------------------------------------------
    # 自动控制
    # ----------------------------------------------------------
    def _apply_control(self, llm_input: dict, reason: str = ""):
        """
        根据比对结果自动下发设备控制指令。
        
        节能策略：
        - energy_saving: 无人→强制关闭（最大节能）
        - comfort_adjust: 有人→按基准值微调（平衡舒适与节能）
        """
        scenario = llm_input.get("scenario", "")
        baseline = llm_input.get("baseline_status", {})
        real = llm_input.get("real_status", {})
        target_fan = baseline.get("fan", 0)
        target_light = baseline.get("light", 0)
        real_fan = real.get("fan", 0)
        real_light = real.get("light", 0)

        action_parts = []
        executed = False

        if not llm_input.get("trigger"):
            # 无触发 → 只更新原因和时间，保持上一次的动作和状态
            self._control_status["reason"] = reason or "一切正常，设备无需调整"
            self._control_status["time"] = llm_input.get("time", "")
            self._control_status["scenario"] = scenario
            return

        if scenario not in ("energy_saving", "comfort_adjust"):
            return

        # 节能策略细化
        if scenario == "energy_saving":
            # 无人但设备运行 → 强制关闭（最大节能）
            if real_fan > 0:
                action_parts.append(f"风扇{real_fan}档→0档")
                target_fan = 0
            if real_light > 0:
                action_parts.append(f"小灯{real_light}档→0档")
                target_light = 0
            print(f"  [节能] 无人状态，关闭所有设备")

        elif scenario == "comfort_adjust":
            # 有人状态下的节能调整
            if real_fan > target_fan:
                action_parts.append(f"风扇{real_fan}档→{target_fan}档")
                print(f"  [节能] 风扇从{real_fan}档降至{target_fan}档")
            elif real_fan < target_fan:
                action_parts.append(f"风扇{real_fan}档→{target_fan}档")
                print(f"  [舒适] 风扇从{real_fan}档升至{target_fan}档")

            if real_light > target_light:
                action_parts.append(f"小灯{real_light}档→{target_light}档")
                print(f"  [节能] 灯光从{real_light}档降至{target_light}档")
            elif real_light < target_light:
                action_parts.append(f"小灯{real_light}档→{target_light}档")
                print(f"  [舒适] 灯光从{real_light}档升至{target_light}档")

        action_text = "；".join(action_parts) if action_parts else "无动作"

        # 直接调用 /set_command API，与前端按钮控制完全一致
        try:
            import urllib.request
            cmd_data = json.dumps({
                "fan_level": target_fan,
                "light_level": target_light
            }).encode("utf-8")
            req = urllib.request.Request(
                "http://127.0.0.1:8080/set_command",
                data=cmd_data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=5)
            result = json.loads(resp.read().decode("utf-8"))
            executed = result.get("success", False)
            print(f"  [Control] 下发指令: fan={target_fan}, light={target_light} → {result.get('msg', 'OK')}")
        except Exception as e:
            print(f"  [Control] 指令下发失败: {e}")

        # 存储控制状态，供前端查询
        self._control_status = {
            "reason": reason or "自动控制调整",
            "action": action_text,
            "executed": executed,
            "time": llm_input.get("time", ""),
            "scenario": scenario,
        }

    # ----------------------------------------------------------
    # 轮询控制
    # ----------------------------------------------------------
    def start_polling(self, interval: int = 30):
        """启动后台轮询线程（单例保护，防止重复启动）"""
        if self._running:
            print("[Behavior] 轮询已在运行中，跳过")
            return

        # 每次启动创建新的 Event，确保旧线程的 stop 信号不受影响
        self._stop_event = threading.Event()
        self._running = True
        stop_event = self._stop_event  # 捕获引用，防止后续 start_polling 覆盖

        def _loop():
            print(f"[Behavior] 轮询已启动，间隔 {interval}s")
            # 使用 Event.wait 替代 time.sleep，关闭时可立即中断（无需等待 sleep 结束）
            while not stop_event.wait(interval):
                try:
                    print(f"[Behavior] [轮询触发] 自动控制开关状态: {_get_control_switch()}")
                    self.analyze_once()
                except Exception as e:
                    print(f"[Behavior] 分析异常: {e}")

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_polling(self):
        """停止轮询（立即中断，无需等待 sleep 结束）"""
        self._stop_event.set()
        self._running = False
        print("[Behavior] 轮询已停止")

    # ----------------------------------------------------------
    # 结果获取
    # ----------------------------------------------------------
    @property
    def latest_result(self) -> dict | None:
        return self._latest_result

    @property
    def control_status(self) -> dict:
        """获取最新控制状态，供前端 AI 状态卡片查询"""
        return self._control_status

    def get_latest_json(self) -> str:
        if self._latest_result is None:
            return json.dumps({"status": "waiting", "msg": "尚未完成首次分析"}, ensure_ascii=False)
        return json.dumps(self._latest_result, ensure_ascii=False, indent=2)


# ============================================================
# 自测（需要有数据库数据）
# ============================================================
if __name__ == "__main__":
    svc = BehaviorAnalysisService()
    result = svc.analyze_once()
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("数据库数据不足，请先运行 app.py 接收传感器数据")
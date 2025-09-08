from importlib import import_module

def test_planner_module_available():
    # 基础存在性测试：确保项目内有 planner 模块可导入
    try:
        import_module("planner")
    except Exception as e:
        # 允许用户先合并源码后再运行 CI，这里仅做冒烟提示
        assert False, f"无法导入 planner 模块，请确认源码已包含：{e}"

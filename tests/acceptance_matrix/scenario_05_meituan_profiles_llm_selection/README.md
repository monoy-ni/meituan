# 05 mock 美团评价与 LLM 商户组合验收

## 目标

验证 mock 美团商户介绍、用户评价摘要、评分等画像会进入 LLM 商户组合器；LLM 只能从候选商户中选择，并能驱动主题局的完整组合。

## 覆盖点

- `merchant_profile()` 生成 mock 评价和商户介绍
- LLM prompt 包含评分、评价摘要、商户介绍
- LLM 返回的商户 ID 会过滤掉编造 ID
- 被 LLM 选中的餐饮、游乐、休闲商户进入主题局路线

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_05_meituan_profiles_llm_selection
```

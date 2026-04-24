# 監査観点カタログ: governance

統制監査の主データは `mappings/governance-controls.json`、逆引きは `index/controls.json`、本文正本は `corpus/*.toon` にある。

人間向けの簡易一覧:

| control_id | 監査項目 | 主な参照 section |
|---|---|---|
| GOV-01 | セキュリティ方針 | `ipa-requirements-guide.overview`, `nist-csf-2-0.govern` |
| GOV-02 | 資産管理 | `nist-csf-2-0.identify`, `ipa-requirements-guide.step_1_system_characteristics` |
| GOV-03 | 権限管理 | `ipa-requirements-guide.step_3_controls`, `nist-sp-800-53-r5.access_and_identity` |
| GOV-04 | 変更管理 | `ipa-nfr-grade.procedure`, `nist-sp-800-53-r5.audit_and_configuration` |
| GOV-05 | インシデント対応 | `nist-csf-2-0.respond`, `nist-sp-800-53-r5.incident_and_recovery` |
| GOV-06 | 復旧と事業継続 | `ipa-nfr-grade.grade_2018_artifacts`, `nist-csf-2-0.recover` |
| GOV-07 | ログ保存方針 | `ipa-requirements-guide.step_3_controls`, `nist-sp-800-53-r5.audit_and_configuration` |
| GOV-08 | 委託先管理 | `ipa-requirements-guide.step_2_risk_and_usability`, `nist-sp-800-53-r5.acquisition_and_supply_chain` |
| GOV-09 | 教育と訓練 | `ipa-safe-website.chapter_3_failure_examples`, `nist-sp-800-53-r5.risk_and_people` |
| GOV-10 | リスク評価 | `ipa-requirements-guide.step_2_risk_and_usability`, `nist-csf-2-0.identify` |
| GOV-11 | データ管理 | `ipa-requirements-guide.step_1_system_characteristics`, `nist-sp-800-53-r5.data_and_system_protection` |
| GOV-12 | 監査可能性 | `ipa-nfr-grade.expected_effects`, `nist-csf-2-0.profiles_and_tiers`, `nist-sp-800-53-r5.audit_and_configuration` |

詳細な checkpoint、優先度、関連標準文書、関連 section は JSON を参照する。

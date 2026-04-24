# 監査観点カタログ: system

技術監査の主データは `mappings/system-controls.json`、逆引きは `index/controls.json`、本文正本は `corpus/*.toon` にある。

人間向けの簡易一覧:

| control_id | 監査項目 | 主な参照 section |
|---|---|---|
| SYS-01 | 認証認可 | `ipa-safe-website.chapter_1_security_implementation`, `nist-csf-2-0.protect`, `nist-sp-800-53-r5.access_and_identity` |
| SYS-02 | セッション管理 | `ipa-safe-website.chapter_1_security_implementation`, `nist-sp-800-53-r5.access_and_identity` |
| SYS-03 | 入力検証 | `ipa-safe-website.chapter_1_security_implementation`, `ipa-safe-website.supplement_safe_sql` |
| SYS-04 | シークレット管理 | `ipa-requirements-guide.step_3_controls`, `nist-csf-2-0.protect` |
| SYS-05 | 暗号化 | `ipa-requirements-guide.overview`, `nist-sp-800-53-r5.data_and_system_protection` |
| SYS-06 | ログと監査証跡 | `ipa-safe-website.chapter_2_site_wide_practices`, `nist-sp-800-53-r5.audit_and_configuration` |
| SYS-07 | 脆弱性管理 | `ipa-safe-website.supplement_web_health_check`, `ipa-nfr-grade.related_materials` |
| SYS-08 | 設定と IaC 管理 | `ipa-nfr-grade.procedure`, `nist-sp-800-53-r5.audit_and_configuration` |
| SYS-09 | CI/CD 保護 | `ipa-nfr-grade.procedure`, `nist-sp-800-53-r5.acquisition_and_supply_chain` |
| SYS-10 | ネットワーク境界 | `ipa-requirements-guide.step_2_risk_and_usability`, `nist-sp-800-53-r5.data_and_system_protection` |
| SYS-11 | データ保護 | `ipa-requirements-guide.overview`, `nist-csf-2-0.protect` |
| SYS-12 | バックアップと復旧 | `ipa-nfr-grade.grade_2018_artifacts`, `nist-csf-2-0.recover` |
| SYS-13 | 監視と検知 | `ipa-safe-website.chapter_2_site_wide_practices`, `nist-csf-2-0.detect` |

詳細な checkpoint、優先度、関連標準文書、関連 section は JSON を参照する。

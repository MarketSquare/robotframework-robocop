# Release notes

## [9.0.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.8.0...v9.0.0) (2026-08-26)


### ⚠ BREAKING CHANGES

* replace ReplaceBreakContinue formatter with deprecated-loop-keyword fix ([#1913](https://github.com/MarketSquare/robotframework-robocop/issues/1913))
* restore NormalizeAssignments and DiscardEmptySections formatter removals ([#1909](https://github.com/MarketSquare/robotframework-robocop/issues/1909))
* remove the ReplaceRunKeywordIf formatter ([#1899](https://github.com/MarketSquare/robotframework-robocop/issues/1899))
* **linter:** exclude project rules from ALL selection ([#1874](https://github.com/MarketSquare/robotframework-robocop/issues/1874))
* **formatter:** aligned columns now use the widest cell plus the configured separator width instead of rounding column positions to multiples of four.
* remove the ReplaceEmptyValues formatter ([#1853](https://github.com/MarketSquare/robotframework-robocop/issues/1853))
* remove the RemoveEmptySettings formatter ([#1849](https://github.com/MarketSquare/robotframework-robocop/issues/1849))
* remove the NormalizeComments formatter ([#1845](https://github.com/MarketSquare/robotframework-robocop/issues/1845))
* deprecate DEPR01 `if-can-be-used` (duplicate of DEPR08) ([#1823](https://github.com/MarketSquare/robotframework-robocop/issues/1823))
* KeywordDefinition and ResolvedImport no longer have the node attribute with the Robot Framework AST node. It was never read by any rule and cannot be stored in the cache. Use the location attribute to report the issue.
* `robocop check-project` was removed. Select project rules and run `robocop check` instead.
* custom project checkers have to accept the `context` argument in `scan_project(project_source_file, config_manager, context)`.

### Features

* add AlignBDDStatements formatter ([#1886](https://github.com/MarketSquare/robotframework-robocop/issues/1886)) ([cad88b2](https://github.com/MarketSquare/robotframework-robocop/commit/cad88b23d71be79c9a4ae63e4a4e135bf06de0b4))
* add ambiguous-keyword-name project rule (KW06) ([#1826](https://github.com/MarketSquare/robotframework-robocop/issues/1826)) ([8d8c2b4](https://github.com/MarketSquare/robotframework-robocop/commit/8d8c2b4387c813f5fadd2f7cd1d97d36e4344255))
* add args_with_test parameter to AlignTemplatedTestCases ([#1918](https://github.com/MarketSquare/robotframework-robocop/issues/1918)) ([43a1ab8](https://github.com/MarketSquare/robotframework-robocop/commit/43a1ab818ce96f628b459ffee54b04d9c1db8e37))
* add built-in minimal ruleset via extends ([#1911](https://github.com/MarketSquare/robotframework-robocop/issues/1911)) ([d80800e](https://github.com/MarketSquare/robotframework-robocop/commit/d80800e9c570a32a4f6276ee839c110cd787135c))
* add circular-import project rule (IMP08) ([#1828](https://github.com/MarketSquare/robotframework-robocop/issues/1828)) ([ccc04ca](https://github.com/MarketSquare/robotframework-robocop/commit/ccc04cac0f42140fae413824b59f0baac8acaecc))
* add config init command to generate documented config file ([#1893](https://github.com/MarketSquare/robotframework-robocop/issues/1893)) ([b3dae8a](https://github.com/MarketSquare/robotframework-robocop/commit/b3dae8a3a34d9382811b6184622944bad2f003f1))
* add context7.json and automate rules list generation ([#1915](https://github.com/MarketSquare/robotframework-robocop/issues/1915)) ([ddfa67b](https://github.com/MarketSquare/robotframework-robocop/commit/ddfa67bf99513da7c78fe62a4ca0e61b49f34be5))
* add continue-on-failure tag rules ([#1882](https://github.com/MarketSquare/robotframework-robocop/issues/1882)) ([a5d9d88](https://github.com/MarketSquare/robotframework-robocop/commit/a5d9d88d4e9c250b7e364ea1cc336a7adc34d1fb))
* add empty-lines-inside-block rule ([#1891](https://github.com/MarketSquare/robotframework-robocop/issues/1891)) ([0b6c399](https://github.com/MarketSquare/robotframework-robocop/commit/0b6c399663f46551cb5f84ce3649ad31d6b849fe))
* add fix for the deprecated-run-keyword-if rule ([#1898](https://github.com/MarketSquare/robotframework-robocop/issues/1898)) ([a554ae0](https://github.com/MarketSquare/robotframework-robocop/commit/a554ae06fd5b43abb948de5f567de758abc51ec5))
* add fix for the duplicated-variable rule ([#1857](https://github.com/MarketSquare/robotframework-robocop/issues/1857)) ([b7a87ed](https://github.com/MarketSquare/robotframework-robocop/commit/b7a87ed0c7e09c890a18851941aee2e6d9af1941))
* add fix for the else-not-upper-case rule ([#1854](https://github.com/MarketSquare/robotframework-robocop/issues/1854)) ([837a979](https://github.com/MarketSquare/robotframework-robocop/commit/837a9797c718b5c5c4ab1d7ebfda8c39e5c39877))
* add fix for the empty-return rule ([#1846](https://github.com/MarketSquare/robotframework-robocop/issues/1846)) ([f376046](https://github.com/MarketSquare/robotframework-robocop/commit/f37604657c0a7385cded374e2b2dcf9daabe8886))
* add fix for the empty-section rule ([#1841](https://github.com/MarketSquare/robotframework-robocop/issues/1841)) ([013fbf1](https://github.com/MarketSquare/robotframework-robocop/commit/013fbf1e1530d48fa7369779a404116b7b4856ae))
* add fix for the empty-tags rule ([#1842](https://github.com/MarketSquare/robotframework-robocop/issues/1842)) ([c3ab608](https://github.com/MarketSquare/robotframework-robocop/commit/c3ab608affacf87be7bb7229dc70338742879388))
* add fix for the inconsistent-assignment rule ([#1901](https://github.com/MarketSquare/robotframework-robocop/issues/1901)) ([bdad38b](https://github.com/MarketSquare/robotframework-robocop/commit/bdad38bddbff7e12a7ad4fd99983944a08134bab))
* add fix for the inline-if-can-be-used rule ([#1900](https://github.com/MarketSquare/robotframework-robocop/issues/1900)) ([e0abb92](https://github.com/MarketSquare/robotframework-robocop/commit/e0abb925079dda3c8447b8d786e9d9f1f73cfa01))
* add fix for the unnecessary-default-tags rule ([#1850](https://github.com/MarketSquare/robotframework-robocop/issues/1850)) ([7ceb2f0](https://github.com/MarketSquare/robotframework-robocop/commit/7ceb2f03047f2c74989530724074c625209d21ca))
* add fix for the unused-disabler rule ([#1855](https://github.com/MarketSquare/robotframework-robocop/issues/1855)) ([c689701](https://github.com/MarketSquare/robotframework-robocop/commit/c68970153038d17a5dda74372a20ac01683e29e5))
* add fixes for missing-space-after-comment and ignored-data rules ([#1844](https://github.com/MarketSquare/robotframework-robocop/issues/1844)) ([927ac26](https://github.com/MarketSquare/robotframework-robocop/commit/927ac26cf91af7b5ace9b6e972ed5a4aa814ab8d))
* add fixes for the assignment sign and negative condition rules ([#1859](https://github.com/MarketSquare/robotframework-robocop/issues/1859)) ([85b57f8](https://github.com/MarketSquare/robotframework-robocop/commit/85b57f8090945ba4d6fcd81aac0e7766462401d0))
* add fixes for the deprecated-with-name and deprecated-singular-header rules ([#1843](https://github.com/MarketSquare/robotframework-robocop/issues/1843)) ([b11faf1](https://github.com/MarketSquare/robotframework-robocop/commit/b11faf13ed1f21e1db862df581dc4ed512193621))
* add fixes for the duplicated import rules ([#1848](https://github.com/MarketSquare/robotframework-robocop/issues/1848)) ([39ae09a](https://github.com/MarketSquare/robotframework-robocop/commit/39ae09ae0df59364e9a13ddacb26715e479c01c6))
* add fixes for the empty settings rules ([#1840](https://github.com/MarketSquare/robotframework-robocop/issues/1840)) ([6b30059](https://github.com/MarketSquare/robotframework-robocop/commit/6b300599a1d30d0b9bfc821db2ec3564585c8143))
* add fixes for the empty-library-alias and duplicated-library-alias rules ([#1847](https://github.com/MarketSquare/robotframework-robocop/issues/1847)) ([ceb35a9](https://github.com/MarketSquare/robotframework-robocop/commit/ceb35a9a882b6451dbec417244c53b95da59cf87))
* add fixes for the empty-variable and undefined-argument-default rules ([#1852](https://github.com/MarketSquare/robotframework-robocop/issues/1852)) ([619b6d8](https://github.com/MarketSquare/robotframework-robocop/commit/619b6d810180cc0a30f8dbffab809ee429776e14))
* add fixes for the import order rules ([#1856](https://github.com/MarketSquare/robotframework-robocop/issues/1856)) ([1b1e871](https://github.com/MarketSquare/robotframework-robocop/commit/1b1e8719e3ad84bd23adb4914cec3bfee4e19329))
* add fixes for the redundant tag rules ([#1851](https://github.com/MarketSquare/robotframework-robocop/issues/1851)) ([4568238](https://github.com/MarketSquare/robotframework-robocop/commit/456823808b819ad4dd87fe74706b93ac3af89543))
* add fixes for the setting and section name casing rules ([#1858](https://github.com/MarketSquare/robotframework-robocop/issues/1858)) ([2726e05](https://github.com/MarketSquare/robotframework-robocop/commit/2726e052990d63532e62fc9b3fcf2b2b6c2b5ce3))
* add GROUP linter rules ([#1896](https://github.com/MarketSquare/robotframework-robocop/issues/1896)) ([5f016c7](https://github.com/MarketSquare/robotframework-robocop/commit/5f016c741d2f9072fce33866cbb8fc0053345979)), closes [#1159](https://github.com/MarketSquare/robotframework-robocop/issues/1159)
* add group-not-allowed rule ([#1897](https://github.com/MarketSquare/robotframework-robocop/issues/1897)) ([5e0f59f](https://github.com/MarketSquare/robotframework-robocop/commit/5e0f59f99a5b370dc4b1cafb9bc63e5ba337fae9))
* add ignore_docs parameter to line-too-long ([#1892](https://github.com/MarketSquare/robotframework-robocop/issues/1892)) ([255c04e](https://github.com/MarketSquare/robotframework-robocop/commit/255c04ee9da487e7a2399d474be93fbaaacf417e))
* add keyword-not-found project rule (KW05) ([#1827](https://github.com/MarketSquare/robotframework-robocop/issues/1827)) ([6d05e1a](https://github.com/MarketSquare/robotframework-robocop/commit/6d05e1af398257e953574257df2d9ca944b0441c))
* add missing-argument-name project rule with a fix ([#1837](https://github.com/MarketSquare/robotframework-robocop/issues/1837)) ([3484da6](https://github.com/MarketSquare/robotframework-robocop/commit/3484da636533d5fd83242f23480dc1e8c2479a77)), closes [#1677](https://github.com/MarketSquare/robotframework-robocop/issues/1677)
* add missing-keyword-prefix project rule with a fix ([#1838](https://github.com/MarketSquare/robotframework-robocop/issues/1838)) ([1d81fea](https://github.com/MarketSquare/robotframework-robocop/commit/1d81fea269c7ceb897dea508ffb9fdd61a9bf4ad))
* add not-enough-whitespace-around-operator rule ([#1914](https://github.com/MarketSquare/robotframework-robocop/issues/1914)) ([89d8f48](https://github.com/MarketSquare/robotframework-robocop/commit/89d8f480ae17fbd05719835f3763a60294765fdc)), closes [#1762](https://github.com/MarketSquare/robotframework-robocop/issues/1762)
* add plugin functionality ([#1884](https://github.com/MarketSquare/robotframework-robocop/issues/1884)) ([5b4140f](https://github.com/MarketSquare/robotframework-robocop/commit/5b4140fb726f6581d3343fec969da6c1987830f6)), closes [#1538](https://github.com/MarketSquare/robotframework-robocop/issues/1538)
* Add robocop-check-project pre-commit hook ([#1810](https://github.com/MarketSquare/robotframework-robocop/issues/1810)) ([315368d](https://github.com/MarketSquare/robotframework-robocop/commit/315368dd6cbda9966669a1764716dda227a05e65))
* add support for test case metadata ([#1889](https://github.com/MarketSquare/robotframework-robocop/issues/1889)) ([1f74d72](https://github.com/MarketSquare/robotframework-robocop/commit/1f74d72a6b9418e60e4c3718578138497b4b377b))
* add unresolved-library-import project rule ([#1832](https://github.com/MarketSquare/robotframework-robocop/issues/1832)) ([2e11e0b](https://github.com/MarketSquare/robotframework-robocop/commit/2e11e0b4c154c73e69454dc30ade9fc0a97181bf))
* add unused-library-import rule ([#1825](https://github.com/MarketSquare/robotframework-robocop/issues/1825)) ([20f76ad](https://github.com/MarketSquare/robotframework-robocop/commit/20f76ad41e1e1f60e0a6d46fa094a6ac6fd591cb))
* allow to skip report file generation on empty results ([#1835](https://github.com/MarketSquare/robotframework-robocop/issues/1835)) ([e198ea5](https://github.com/MarketSquare/robotframework-robocop/commit/e198ea593eb9bc97e9170f075013441b804086a3)), closes [#1332](https://github.com/MarketSquare/robotframework-robocop/issues/1332)
* apply fixes reported by project level rules ([#1836](https://github.com/MarketSquare/robotframework-robocop/issues/1836)) ([9aa174f](https://github.com/MarketSquare/robotframework-robocop/commit/9aa174f6ac90b3388f49ee718ac30812eaa75f72))
* cache imported library keywords between runs ([#1830](https://github.com/MarketSquare/robotframework-robocop/issues/1830)) ([93a9fad](https://github.com/MarketSquare/robotframework-robocop/commit/93a9fad662c22bfda3cb96ca1dbcdb42b72f388f))
* cache project analysis data between runs ([#1833](https://github.com/MarketSquare/robotframework-robocop/issues/1833)) ([642a61c](https://github.com/MarketSquare/robotframework-robocop/commit/642a61c611073fbbcf770a5e4addf8c0c5255c15))
* check VAR assignment sign in inconsistent-assignment rule ([#1902](https://github.com/MarketSquare/robotframework-robocop/issues/1902)) ([bd3137a](https://github.com/MarketSquare/robotframework-robocop/commit/bd3137a239545d8071fd5c33cae5b09c46d3b4a1))
* deprecate DEPR01 `if-can-be-used` (duplicate of DEPR08) ([#1823](https://github.com/MarketSquare/robotframework-robocop/issues/1823)) ([14654ec](https://github.com/MarketSquare/robotframework-robocop/commit/14654ec00ed97913742b0c09efd13031dd2baebd))
* **formatter:** use concise alignment padding ([#1864](https://github.com/MarketSquare/robotframework-robocop/issues/1864)) ([d4741c7](https://github.com/MarketSquare/robotframework-robocop/commit/d4741c7a0cbd185ffaf443776b0f67ec87f7b332))
* improve config init output for severity, target version and project ([#1894](https://github.com/MarketSquare/robotframework-robocop/issues/1894)) ([4495744](https://github.com/MarketSquare/robotframework-robocop/commit/4495744ae732eaed0547f2309eb916c6fd65affc))
* **linter:** add empty template data line rule ([#1865](https://github.com/MarketSquare/robotframework-robocop/issues/1865)) ([989bd4e](https://github.com/MarketSquare/robotframework-robocop/commit/989bd4eb36a134568c6556ae216b4708e8dd2f46))
* **linter:** add fix for wrong-case-in-keyword-name and wrong-case-in-keyword-call ([#1860](https://github.com/MarketSquare/robotframework-robocop/issues/1860)) ([5084c43](https://github.com/MarketSquare/robotframework-robocop/commit/5084c43c1cf63dfda72de1a35d660fba932ddd2d))
* **linter:** add fixes for malformed separators ([#1862](https://github.com/MarketSquare/robotframework-robocop/issues/1862)) ([4a40f9f](https://github.com/MarketSquare/robotframework-robocop/commit/4a40f9f3ac3296fc67efb03607f692174de6f3eb))
* **linter:** check automatic variable availability ([#1867](https://github.com/MarketSquare/robotframework-robocop/issues/1867)) ([b2ffe06](https://github.com/MarketSquare/robotframework-robocop/commit/b2ffe0661b767b066de2e13d95588f1e3f432664))
* **linter:** detect variables in documentation ([#1866](https://github.com/MarketSquare/robotframework-robocop/issues/1866)) ([05a73ed](https://github.com/MarketSquare/robotframework-robocop/commit/05a73ed8055e9d64871e7aed4fd9402b3fb8f063))
* **linter:** exclude project rules from ALL selection ([#1874](https://github.com/MarketSquare/robotframework-robocop/issues/1874)) ([3658113](https://github.com/MarketSquare/robotframework-robocop/commit/36581135dbd06cc6eaa9f7b8716efe5e7dbc49ee))
* **linter:** load libraries in process unless --library-workers is used ([#1872](https://github.com/MarketSquare/robotframework-robocop/issues/1872)) ([2f51d75](https://github.com/MarketSquare/robotframework-robocop/commit/2f51d7546e922012bcc355c32cd7c42099ed430e))
* project level context with rules using it ([#1822](https://github.com/MarketSquare/robotframework-robocop/issues/1822)) ([527c5b9](https://github.com/MarketSquare/robotframework-robocop/commit/527c5b980436129df81679754fed6832a8a1b642))
* reevaluate rule severities for upcoming rulesets change ([#1910](https://github.com/MarketSquare/robotframework-robocop/issues/1910)) ([5b4e2ed](https://github.com/MarketSquare/robotframework-robocop/commit/5b4e2ede5765c7eb8da378729846f3321b6e45d1))
* remove the NormalizeComments formatter ([#1845](https://github.com/MarketSquare/robotframework-robocop/issues/1845)) ([d0c64a1](https://github.com/MarketSquare/robotframework-robocop/commit/d0c64a1163aee224ce98b3a2838e9629d83fd7a3))
* remove the RemoveEmptySettings formatter ([#1849](https://github.com/MarketSquare/robotframework-robocop/issues/1849)) ([d3d570f](https://github.com/MarketSquare/robotframework-robocop/commit/d3d570f6138768b81fb49cbd349c38731e799d7d))
* remove the ReplaceEmptyValues formatter ([#1853](https://github.com/MarketSquare/robotframework-robocop/issues/1853)) ([4767d7c](https://github.com/MarketSquare/robotframework-robocop/commit/4767d7cb40daafa3e8437961db7d61502e24cb0a))
* remove the ReplaceRunKeywordIf formatter ([#1899](https://github.com/MarketSquare/robotframework-robocop/issues/1899)) ([bae1b01](https://github.com/MarketSquare/robotframework-robocop/commit/bae1b0103e626ad4b08073172db0f43f59ded393))
* replace ReplaceBreakContinue formatter with deprecated-loop-keyword fix ([#1913](https://github.com/MarketSquare/robotframework-robocop/issues/1913)) ([ac60ec8](https://github.com/MarketSquare/robotframework-robocop/commit/ac60ec8b398c01ef2fdde782b2f4937c8bcd95b0))
* restore NormalizeAssignments and DiscardEmptySections formatter removals ([#1909](https://github.com/MarketSquare/robotframework-robocop/issues/1909)) ([7f5e14b](https://github.com/MarketSquare/robotframework-robocop/commit/7f5e14b4f3fad429e787213e5243b0e5f9ce02f1))
* run project rules as a part of the check command ([#1824](https://github.com/MarketSquare/robotframework-robocop/issues/1824)) ([ecd971b](https://github.com/MarketSquare/robotframework-robocop/commit/ecd971bf78735e2f0b7323002cde7ffa90bf2aa9))
* select all project rules with PROJECT keyword ([#1834](https://github.com/MarketSquare/robotframework-robocop/issues/1834)) ([7ea17a6](https://github.com/MarketSquare/robotframework-robocop/commit/7ea17a6f81aac6d116322039e2a005e0fdc7d125))
* support custom reports ([#1885](https://github.com/MarketSquare/robotframework-robocop/issues/1885)) ([8e43ffb](https://github.com/MarketSquare/robotframework-robocop/commit/8e43ffb8880c03166dec00909b249baa5420b5bf)), closes [#1115](https://github.com/MarketSquare/robotframework-robocop/issues/1115)


### Bug Fixes

* align only first column of documentation in AlignSettingsSection ([#1890](https://github.com/MarketSquare/robotframework-robocop/issues/1890)) ([1eff121](https://github.com/MarketSquare/robotframework-robocop/commit/1eff121de8a68a97a2dcae2fec65194f6fe1c741))
* File-wide rule NAME15 prints source code on report ([#1871](https://github.com/MarketSquare/robotframework-robocop/issues/1871)) ([e45fd08](https://github.com/MarketSquare/robotframework-robocop/commit/e45fd086f1d7c7a867c1ceabe587292ffd78be5b))
* handle comments between keywords in SmartSortKeywords ([#1888](https://github.com/MarketSquare/robotframework-robocop/issues/1888)) ([a3c86bc](https://github.com/MarketSquare/robotframework-robocop/commit/a3c86bc431966558b5d734fb92569fd847735369)), closes [#1718](https://github.com/MarketSquare/robotframework-robocop/issues/1718)
* keep comments with statement in IndentNestedKeywords ([#1919](https://github.com/MarketSquare/robotframework-robocop/issues/1919)) ([7be0805](https://github.com/MarketSquare/robotframework-robocop/commit/7be08058def906ce713a95fb838bd2c3389399c8)), closes [#1507](https://github.com/MarketSquare/robotframework-robocop/issues/1507)
* Keywords defined in multiple resources ignored even when prefixed ([#1881](https://github.com/MarketSquare/robotframework-robocop/issues/1881)) ([35b4952](https://github.com/MarketSquare/robotframework-robocop/commit/35b4952972c615efca89259fdba117b090910a03))
* **linter:** match library keywords with embedded arguments ([#1869](https://github.com/MarketSquare/robotframework-robocop/issues/1869)) ([73e9bba](https://github.com/MarketSquare/robotframework-robocop/commit/73e9bbadd92169f43d6a32c5e357c93b0c50c407))
* MyPy error on PathSpec expects no type ([#1879](https://github.com/MarketSquare/robotframework-robocop/issues/1879)) ([8014877](https://github.com/MarketSquare/robotframework-robocop/commit/80148774abfdca8b203d76b0e60f74c036b62b80))
* replace deprecated GitWildMatchPattern with GitIgnoreSpec ([#1887](https://github.com/MarketSquare/robotframework-robocop/issues/1887)) ([5a2090c](https://github.com/MarketSquare/robotframework-robocop/commit/5a2090c1e4980cffdf7b7163642f42c7a79a7dd7))
* report empty and unterminated GROUP parse errors ([#1895](https://github.com/MarketSquare/robotframework-robocop/issues/1895)) ([227874a](https://github.com/MarketSquare/robotframework-robocop/commit/227874afa315a11e74542ac50ae548fec99c69d8)), closes [#1159](https://github.com/MarketSquare/robotframework-robocop/issues/1159)
* resolve run keywords called with a BDD prefix ([#1877](https://github.com/MarketSquare/robotframework-robocop/issues/1877)) ([7500113](https://github.com/MarketSquare/robotframework-robocop/commit/75001135cd2c138dced8b535f769cc2fb7f62f1b))
* resolve strict mypy baseline ([#1863](https://github.com/MarketSquare/robotframework-robocop/issues/1863)) ([d17b294](https://github.com/MarketSquare/robotframework-robocop/commit/d17b2947edd751218c27d705007ed5f43b2a9437))
* silence library import output during project analysis ([#1876](https://github.com/MarketSquare/robotframework-robocop/issues/1876)) ([a07689e](https://github.com/MarketSquare/robotframework-robocop/commit/a07689e6bf4adf5630a798ec79eb4da1e7f8ba25))
* Use resolved library name in project rules instead of path ([#1880](https://github.com/MarketSquare/robotframework-robocop/issues/1880)) ([367a488](https://github.com/MarketSquare/robotframework-robocop/commit/367a4881fcf674d24884eb36e282ac50353b04ed))


### Documentation

* document branch, commit and PR naming conventions ([#1873](https://github.com/MarketSquare/robotframework-robocop/issues/1873)) ([4064693](https://github.com/MarketSquare/robotframework-robocop/commit/4064693b41568702de0e7340ff8a20233fe49912))
* **linter:** point whitespace rules at robocop format ([#1861](https://github.com/MarketSquare/robotframework-robocop/issues/1861)) ([6fb9b48](https://github.com/MarketSquare/robotframework-robocop/commit/6fb9b48f74d32dea4dbce1767fa3673b6f113f59))
* mark project rules in the rules list ([#1829](https://github.com/MarketSquare/robotframework-robocop/issues/1829)) ([09dd54a](https://github.com/MarketSquare/robotframework-robocop/commit/09dd54afcb64e09cca9a9f52015ac71a658b8fb5))


### Performance

* cache resolved paths in project analysis ([#1875](https://github.com/MarketSquare/robotframework-robocop/issues/1875)) ([d20389c](https://github.com/MarketSquare/robotframework-robocop/commit/d20389c512cbbaf1dc986d72d8464d9bbf7db71a))


### Refactoring

* merge control flow checkers into single ControlFlowChecker ([#1818](https://github.com/MarketSquare/robotframework-robocop/issues/1818)) ([fb4afc2](https://github.com/MarketSquare/robotframework-robocop/commit/fb4afc2c9fc530fa9d0bd61ef7675283eb4ea2be))
* merge deprecated statement checker into settings checker ([#1820](https://github.com/MarketSquare/robotframework-robocop/issues/1820)) ([883f6fc](https://github.com/MarketSquare/robotframework-robocop/commit/883f6fcec724e33215f94f15353fcc7e94c99b59))
* merge keyword and variable naming checkers ([#1819](https://github.com/MarketSquare/robotframework-robocop/issues/1819)) ([ec7d75f](https://github.com/MarketSquare/robotframework-robocop/commit/ec7d75f273ec15deed1f8e96cb0016636c8f5ece))
* merge keyword argument checkers into a single checker ([#1808](https://github.com/MarketSquare/robotframework-robocop/issues/1808)) ([67f7ab0](https://github.com/MarketSquare/robotframework-robocop/commit/67f7ab02908b28954cbe9f7b31f1636d0a8cab94))
* merge keyword body checkers into a single checker ([#1812](https://github.com/MarketSquare/robotframework-robocop/issues/1812)) ([812d158](https://github.com/MarketSquare/robotframework-robocop/commit/812d158645ea44dd29fef5443b6bb59c656eb7d7))
* merge keyword call checkers into a single checker ([#1807](https://github.com/MarketSquare/robotframework-robocop/issues/1807)) ([a2652a0](https://github.com/MarketSquare/robotframework-robocop/commit/a2652a01de134a1d7985dc99ed41634636b282fd))
* merge project checkers sharing keyword usage iteration ([#1917](https://github.com/MarketSquare/robotframework-robocop/issues/1917)) ([9c41a2a](https://github.com/MarketSquare/robotframework-robocop/commit/9c41a2a76abe94f6621b0a2ecbc800812a89421e))
* merge raw file checkers into a single checker ([#1806](https://github.com/MarketSquare/robotframework-robocop/issues/1806)) ([98e2aff](https://github.com/MarketSquare/robotframework-robocop/commit/98e2aff09c6e9e1d97a56f37bee1d0317b1dd94e))
* merge section-level checkers into single SectionsChecker ([#1813](https://github.com/MarketSquare/robotframework-robocop/issues/1813)) ([88c0b53](https://github.com/MarketSquare/robotframework-robocop/commit/88c0b53a6e000c06243a9a94e438077d4cb7a830))
* merge settings checkers into single SettingsChecker ([#1817](https://github.com/MarketSquare/robotframework-robocop/issues/1817)) ([33f335a](https://github.com/MarketSquare/robotframework-robocop/commit/33f335a8cdfc9d193cc4c185ede586c469e4636b))
* merge tag checkers into single TagsChecker ([#1815](https://github.com/MarketSquare/robotframework-robocop/issues/1815)) ([852b450](https://github.com/MarketSquare/robotframework-robocop/commit/852b450b4aa28dcb21c5331666550f6b860879be))
* merge test case and keyword checkers into TestCaseKeywordChecker ([#1814](https://github.com/MarketSquare/robotframework-robocop/issues/1814)) ([280b297](https://github.com/MarketSquare/robotframework-robocop/commit/280b297b297159b4f7a0df2052bb7a32fb037c0a))
* merge variable statement checkers into single VariablesChecker ([#1816](https://github.com/MarketSquare/robotframework-robocop/issues/1816)) ([6d18ea2](https://github.com/MarketSquare/robotframework-robocop/commit/6d18ea2300edc3b4ed55d22bf2edd5eb27e37909))
* move linter checkers to a dedicated package ([#1821](https://github.com/MarketSquare/robotframework-robocop/issues/1821)) ([cc15ac3](https://github.com/MarketSquare/robotframework-robocop/commit/cc15ac3849b19e56dfb8a4825a32a851e3fc31d4))

## [9.0.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.8.0...v9.0.0) (2026-08-21)

More detailed notes regarding 9.0.0 [here](9.0.0.md).

## [8.8.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.7.0...v8.8.0) (2026-08-12)


### Features

* Support Robot Framework 7.5 by relaxing upper version bound to &lt;7.6 ([#1804](https://github.com/MarketSquare/robotframework-robocop/issues/1804)) ([de41ead](https://github.com/MarketSquare/robotframework-robocop/commit/de41eadcf45023fe8455171f9d8b427e7bef66d0))

## [8.7.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.6.0...v8.7.0) (2026-08-12)


### Features

* add --verbose option to list formatters command to print configurables ([#1802](https://github.com/MarketSquare/robotframework-robocop/issues/1802)) ([d425866](https://github.com/MarketSquare/robotframework-robocop/commit/d425866a062c7f22aca5ff680920104808e580e9))
* Make list rules more verbose; print configurables (with --verbose) and default/modified values ([#1799](https://github.com/MarketSquare/robotframework-robocop/issues/1799)) ([5d94399](https://github.com/MarketSquare/robotframework-robocop/commit/5d9439917486c373fdef9f91dde204bc1c34b0ab))


### Bug Fixes

* robocop docs formatters fails to print non-default formatters ([#1801](https://github.com/MarketSquare/robotframework-robocop/issues/1801)) ([703ebeb](https://github.com/MarketSquare/robotframework-robocop/commit/703ebebe60b88e324b875eb99dfbdb9771bbfe07))

## [8.6.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.5.0...v8.6.0) (2026-08-06)


### Features

* **SplitTooLongLine:** add per-type align_new_line options ([#1796](https://github.com/MarketSquare/robotframework-robocop/issues/1796)) ([7135db6](https://github.com/MarketSquare/robotframework-robocop/commit/7135db615ef42f6a1b8771255c9022e720e117ac))

## [8.5.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.4.1...v8.5.0) (2026-07-31)


### Features

* support --config option in list rules/formatters docs options ([#1791](https://github.com/MarketSquare/robotframework-robocop/issues/1791)) ([61024dd](https://github.com/MarketSquare/robotframework-robocop/commit/61024dda84e55590f59c0daaf6d9a79e20e6a038))

## [8.4.1](https://github.com/MarketSquare/robotframework-robocop/compare/v8.4.0...v8.4.1) (2026-07-30)


### Bug Fixes

* mark --ignore values as matched for rules below --threshold ([#1786](https://github.com/MarketSquare/robotframework-robocop/issues/1786)) ([70d0ab6](https://github.com/MarketSquare/robotframework-robocop/commit/70d0ab69f42c3b7dbd4f61605929c8122771a52c)), closes [#1775](https://github.com/MarketSquare/robotframework-robocop/issues/1775)

## [8.4.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.3.2...v8.4.0) (2026-07-30)


### Features

* keep first setting argument on the setting line in SplitTooLongLine ([#1784](https://github.com/MarketSquare/robotframework-robocop/issues/1784)) ([59416c8](https://github.com/MarketSquare/robotframework-robocop/commit/59416c86baa8dbe0d5ac0b342bfb06194038e157)), closes [#1723](https://github.com/MarketSquare/robotframework-robocop/issues/1723)

## [8.3.2](https://github.com/MarketSquare/robotframework-robocop/compare/v8.3.1...v8.3.2) (2026-06-17)


### Bug Fixes

* respect `fmt: off` when aligning comments in keyword/test-case aligners ([#1771](https://github.com/MarketSquare/robotframework-robocop/issues/1771)) ([d7f7dba](https://github.com/MarketSquare/robotframework-robocop/commit/d7f7dba3b1c4805fa6379e1076c4845e083dc0e4))

## [8.3.1](https://github.com/MarketSquare/robotframework-robocop/compare/v8.3.0...v8.3.1) (2026-06-17)


### Bug Fixes

* stop AlignKeywords/TestCasesSection from aligning comments outside test cases and keywords ([#1768](https://github.com/MarketSquare/robotframework-robocop/issues/1768)) ([ff98d1b](https://github.com/MarketSquare/robotframework-robocop/commit/ff98d1bc90c442717ff99cd08caaf0304e7a433d))

## [8.3.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.11...v8.3.0) (2026-06-17)


### Features

* Add `test_types` option to AlignTestCasesSection for templated/non-templated tests ([#1764](https://github.com/MarketSquare/robotframework-robocop/issues/1764)) ([acfdb45](https://github.com/MarketSquare/robotframework-robocop/commit/acfdb4563e0f5938b678565cbe856b496f61d905))

## [8.2.11](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.10...v8.2.11) (2026-06-12)


### Bug Fixes

* add deptry dependency check ([#1761](https://github.com/MarketSquare/robotframework-robocop/issues/1761)) ([4990e53](https://github.com/MarketSquare/robotframework-robocop/commit/4990e53a26f9ba065b2440f92f3e251989912628))
* References to upstream `click` causing further side effects ([#1754](https://github.com/MarketSquare/robotframework-robocop/issues/1754)) ([#1755](https://github.com/MarketSquare/robotframework-robocop/issues/1755)) ([4007e29](https://github.com/MarketSquare/robotframework-robocop/commit/4007e291c49736d645958dcaacfd97ec9f0d2f12))

## [8.2.10](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.9...v8.2.10) (2026-06-05)


### Bug Fixes

* Fix unused-variable false positive for variables consumed only in [Teardown] ([#1757](https://github.com/MarketSquare/robotframework-robocop/issues/1757)) ([a936fd3](https://github.com/MarketSquare/robotframework-robocop/commit/a936fd3c45d1fec09b0eaecdd3f8fbc9210a2fa7))

## [8.2.9](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.8...v8.2.9) (2026-05-26)


### Bug Fixes

* add click as explicit dependency ([#1751](https://github.com/MarketSquare/robotframework-robocop/issues/1751)) ([47ee186](https://github.com/MarketSquare/robotframework-robocop/commit/47ee186cc0cbeef8cf97751bac7555a58b1c7c6e))

## [8.2.8](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.7...v8.2.8) (2026-05-11)


### Bug Fixes

* Fix documentation typos & add documentation linter ([#1738](https://github.com/MarketSquare/robotframework-robocop/issues/1738)) ([2a45e93](https://github.com/MarketSquare/robotframework-robocop/commit/2a45e93432c94d1b8bf76b999172b1f582053e6e))
* Fix formatting result incorrectly cached in no overwrite modes (--diff/--no-overwrite) ([#1742](https://github.com/MarketSquare/robotframework-robocop/issues/1742)) ([1d7fadc](https://github.com/MarketSquare/robotframework-robocop/commit/1d7fadcc8b247564b1a07246edb550776a24a3b5))

## [8.2.7](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.6...v8.2.7) (2026-04-14)


### Bug Fixes

* Keyword naming rules with library import with underscores is now detected properly ([#1734](https://github.com/MarketSquare/robotframework-robocop/issues/1734)) ([a86b1d4](https://github.com/MarketSquare/robotframework-robocop/commit/a86b1d4133008a844ac45268076874f85189390b))

## [8.2.6](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.5...v8.2.6) (2026-04-13)


### Bug Fixes

* ensure that configuration files are loaded in the order (robocop.toml &gt; robot.toml &gt; pyproject.toml) ([#1729](https://github.com/MarketSquare/robotframework-robocop/issues/1729)) ([b7e041f](https://github.com/MarketSquare/robotframework-robocop/commit/b7e041f314e375035fc61d29348425df8168dc89))
* pygments 2.20.0 failing to build our documentaton ([#1731](https://github.com/MarketSquare/robotframework-robocop/issues/1731)) ([e6a5945](https://github.com/MarketSquare/robotframework-robocop/commit/e6a594589b9e23d24c505b47fd4bd7f090d98130))

## [8.2.5](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.4...v8.2.5) (2026-04-07)


### Bug Fixes

* Fix section-out-of-order not supporting comments section ([#1725](https://github.com/MarketSquare/robotframework-robocop/issues/1725)) ([56f0ab2](https://github.com/MarketSquare/robotframework-robocop/commit/56f0ab2a2dffbabddfccf5473be369b8252cf9de))

## [8.2.4](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.3...v8.2.4) (2026-03-27)


### Bug Fixes

* Add missing robot:exit-on-failure tag to reserved tag list ([#1712](https://github.com/MarketSquare/robotframework-robocop/issues/1712)) ([1f2097a](https://github.com/MarketSquare/robotframework-robocop/commit/1f2097a701984439a3a3e5c2583ac37f21d06bb4))

## [8.2.3](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.2...v8.2.3) (2026-03-17)


### Bug Fixes

* Fix missing force-exclude flag from the configuration file ([#1708](https://github.com/MarketSquare/robotframework-robocop/issues/1708)) ([90cea8c](https://github.com/MarketSquare/robotframework-robocop/commit/90cea8c9ee78552e8c86a58297553e6703f50e38))
* Fix unused-variable reported on the FOR loop variable with type ([#1706](https://github.com/MarketSquare/robotframework-robocop/issues/1706)) ([260f4f4](https://github.com/MarketSquare/robotframework-robocop/commit/260f4f44c012266a8fdce06a8c5ece84e4c98383))

## [8.2.2](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.1...v8.2.2) (2026-02-27)


### Bug Fixes

* Fix fatal attribute error when running Robocop ([#1698](https://github.com/MarketSquare/robotframework-robocop/issues/1698)) ([47ac87e](https://github.com/MarketSquare/robotframework-robocop/commit/47ac87eae4a4a789d1bda4159dad285c725b8449))

## [8.2.1](https://github.com/MarketSquare/robotframework-robocop/compare/v8.2.0...v8.2.1) (2026-02-27)


### Bug Fixes

* Fix circular import error due to ConfigManager split from config.py ([#1695](https://github.com/MarketSquare/robotframework-robocop/issues/1695)) ([09e3fda](https://github.com/MarketSquare/robotframework-robocop/commit/09e3fdaa8e83a16b19f49c5f199f728d056fde27))

## [8.2.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.1.1...v8.2.0) (2026-02-22)


### Features

* **mcp:** Allow to pass configuration file path via MCP tools ([#1691](https://github.com/MarketSquare/robotframework-robocop/issues/1691)) ([da5dc6e](https://github.com/MarketSquare/robotframework-robocop/commit/da5dc6e04cda7764608fd10abf4e9e7574836a2e))

## [8.1.1](https://github.com/MarketSquare/robotframework-robocop/compare/v8.1.0...v8.1.1) (2026-02-20)


### Bug Fixes

* Fix unused-variable reported on variable names starting with digit ([#1689](https://github.com/MarketSquare/robotframework-robocop/issues/1689)) ([fc6b78d](https://github.com/MarketSquare/robotframework-robocop/commit/fc6b78de9faa3d61acc0a6e9f8424c0cc4333efa))

## [8.1.0](https://github.com/MarketSquare/robotframework-robocop/compare/v8.0.0...v8.1.0) (2026-02-19)


### Features

* Replace `typer-slim` with `typer` ([#1685](https://github.com/MarketSquare/robotframework-robocop/issues/1685)) ([b83400f](https://github.com/MarketSquare/robotframework-robocop/commit/b83400f5727d4a4b82092319401abdf7fba699e8))


### Bug Fixes

* unused-argument rule raised when argument is used in item access or inline eval ([#1687](https://github.com/MarketSquare/robotframework-robocop/issues/1687)) ([d014a53](https://github.com/MarketSquare/robotframework-robocop/commit/d014a53d32b9effe696fccc993f675efb3724941))

## [8.0.0](https://github.com/MarketSquare/robotframework-robocop/compare/v7.2.0...v8.0.0) (2026-02-11)


More detailed notes regarding 8.0.0 [here](8.0.0.md).

### Breaking changes

* dropped support for Python 3.9
* dropped support for Robot Framework 4
* Deprecated ``deprecated-statement`` rule
* Deprecated ``ReplaceReturns`` formatter
* Deprecated ``AddMissingEnd`` formatter
* refactored source files handling with common ``SourceFile`` class
* redesigned configuration layer for typing safety and OOP friendliness

### Features

* Fixable rules (#1617) (128c849)
* deprecate ``deprecated-statement`` rule and split into new rules
* new rule DEPR08 ``deprecated-run-keyword-if``
* new rule DEPR09 ``deprecated-loop-keyword``
* new rule DEPR10 ``deprecated-return-keyword`` (with a fix)
* new rule DEPR11 ``deprecated-return-setting`` (with a fix)
* Robocop is now more verbose
* Keyword naming rules and formatters quotation handling
* performance improvements (#1611) (eea1c56)
* ``report()`` can be now used from the rule class (#1644) (8aff795)
* Robocop is now fully typed (#1661) (42045dc)
* list rules can now return the result when used from the Python (#1629) (457d135)
* MCP is now aware of local config (#1673) (55e18b6)
* Skip documentation by default in NormalizeSeparators (#1672) (5b1ae35)
* Added or improved support for variable type conversion (#1654) (#1650) (#1651) (#1652) #1653)
* New rule ANN04 ``set-keyword-with-type``
* Add ``case_normalization`` parameter to enforce case by RenameKeywords (#1667) (49a0b02)

### Bug fixes

* add explicit typing-extensions dependency (#1680) (b406f25)
* Fix #1174 expression-can-be-simplified raised for == 0 (#1649) (d0f4985)
* Fix #1422 - ReplaceWithVAR formatter replacing variables with item access (#1648) (a9c3377)
* Fix caching the issues with fixes (#1623) (256874b)
* Fix extend-select matching only on rule id, not on rule name (#1669) (403ff7d)
* Fix format --extend-select not enabling formatters (#1668) (3c76c50)
* Fix not all issue format parameters supported by extended output (#1624) (727c38d)
* Fix too-long-variable-name throwing exception on Set X Variable without arguments (#1675) (3a55663)
* multiple paths passed to robocop check/format command resolving to the same config (#1614) (bdcfd48)
* Fix rst-style urls in the documentation (#1640) (eb1dcab)
* Update RenameVariables formatter so it treats numbers as part of word and does not split on it (#1663) (eddfd96)

## [7.2.0](https://github.com/MarketSquare/robotframework-robocop/compare/v7.1.0...v7.2.0) (2026-01-01)


### Features

* **mcp:** add new tools and improve UX for large codebases ([#1601](https://github.com/MarketSquare/robotframework-robocop/issues/1601)) ([9b1d871](https://github.com/MarketSquare/robotframework-robocop/commit/9b1d871a2c40549de1d2f1b707201da47f6c68a6))
* **mcp:** add response caching and error handling middleware ([#1599](https://github.com/MarketSquare/robotframework-robocop/issues/1599)) ([406cfbe](https://github.com/MarketSquare/robotframework-robocop/commit/406cfbefaa229664fdd39e5265f2f47958aabb64))
* **mcp:** enhance MCP server with batch operations, quality metrics, and improved LLM guidance ([#1593](https://github.com/MarketSquare/robotframework-robocop/issues/1593)) ([c6a853b](https://github.com/MarketSquare/robotframework-robocop/commit/c6a853bd016eff8f65742c79c511fd8712abc1a3))
* Refactor print_issues report to gain 3x perfomance gain on printing ([#1605](https://github.com/MarketSquare/robotframework-robocop/issues/1605)) ([6755d96](https://github.com/MarketSquare/robotframework-robocop/commit/6755d96ceadb0b78a80f6e70e5e262967029fde3))


### Bug Fixes

* **caching:** Fix CLI always overriding cache=true/false in the configuration file ([#1608](https://github.com/MarketSquare/robotframework-robocop/issues/1608)) ([b31a5ef](https://github.com/MarketSquare/robotframework-robocop/commit/b31a5ef95c1d706623656aa3f1417730f8c23034))
* **release:** fix triggering Github workflows from automated scripts ([#1594](https://github.com/MarketSquare/robotframework-robocop/issues/1594)) ([72ce0ff](https://github.com/MarketSquare/robotframework-robocop/commit/72ce0ff36aed05eef362aa0aeed80324b2ec7a8e))

## [7.1.0](https://github.com/MarketSquare/robotframework-robocop/compare/v7.0.0...v7.1.0) (2025-12-23)


### Features

* add commented-out-code detection rule (COM06) ([#1564](https://github.com/MarketSquare/robotframework-robocop/issues/1564)) ([8afa9d2](https://github.com/MarketSquare/robotframework-robocop/commit/8afa9d268d4ca909cf56225992962c39a088f8bf))
* add file-level caching for linter and formatter to skip unchanged files ([#1565](https://github.com/MarketSquare/robotframework-robocop/issues/1565)) ([ceb02cc](https://github.com/MarketSquare/robotframework-robocop/commit/ceb02ccff7cf5316ef8debb5040bfa625981eba0))
* add MCP server for AI assistant integration ([#1583](https://github.com/MarketSquare/robotframework-robocop/issues/1583)) ([c68330a](https://github.com/MarketSquare/robotframework-robocop/commit/c68330a34a740e86388ee540327ed6f1d1fe83fb))
* add three separate rules for variable type annotations (RF 7.3+) ([#1579](https://github.com/MarketSquare/robotframework-robocop/issues/1579)) ([03ef483](https://github.com/MarketSquare/robotframework-robocop/commit/03ef483446a153137035c48f8f6e63ce02cca480))
* automate release process with release-please ([#1571](https://github.com/MarketSquare/robotframework-robocop/issues/1571)) ([4bd6d3f](https://github.com/MarketSquare/robotframework-robocop/commit/4bd6d3f5cddaa4c85085ca87b8960720e77d8dd6))
* **VAR02:** add ignore parameter for unused-variable rule ([#1576](https://github.com/MarketSquare/robotframework-robocop/issues/1576)) ([0c2ebf4](https://github.com/MarketSquare/robotframework-robocop/commit/0c2ebf41a2f43f0cb73e586b3e254c02cdfacf7c))


### Bug Fixes

* Invalid Robocop disabler accepted as disabler for all rules ([#1569](https://github.com/MarketSquare/robotframework-robocop/issues/1569)) ([595ffdb](https://github.com/MarketSquare/robotframework-robocop/commit/595ffdb83a3b50ccebf4883493b221076782836b))
* **mcp:** fix limit handling bugs and add enhancements ([#1589](https://github.com/MarketSquare/robotframework-robocop/issues/1589)) ([0926a4d](https://github.com/MarketSquare/robotframework-robocop/commit/0926a4d114b10bdb8a468a472f1105d9a227c645))


### Documentation

* add annotations rule group to documentation ([#1439](https://github.com/MarketSquare/robotframework-robocop/issues/1439)) ([#1588](https://github.com/MarketSquare/robotframework-robocop/issues/1588)) ([50cbfa7](https://github.com/MarketSquare/robotframework-robocop/commit/50cbfa72cd34997ce0a63aeaaa5e109a05f83bb6))
* Add caching documentation ([#1572](https://github.com/MarketSquare/robotframework-robocop/issues/1572)) ([5d941e8](https://github.com/MarketSquare/robotframework-robocop/commit/5d941e849f5ac84a8208b1d21ccdf861006b4cbc))

## 7.0.0

### Features

- **Breaking change** Add option ``--extend-select`` for linter and formatter ([issue #1546](https://github.com/MarketSquare/robotframework-robocop/issues/1546))

    ``--extend-select`` allows to enable rules and formatters on top of the ``select`` configuration. It can be used to
    retain all default rules or formatters and only add additional ones:
    
    ```
    robocop check --extend-select no-embedded-keyword-arguments
    robocop format --extend-select AlignKeywordsSection --extend-select CustomFormatter
    ```

    Since previous ``--custom-formatters`` formatter option already behaved like a ``--extend-select`` option (which was
    not documented), it is now **deprecated and renamed** to ``--extend-select`` instead.

    It is also recommended to use ``--extend-select`` over ``--configue name.enabled=True``.

- **Breaking change** Split ``wrong-case-in-keyword-name`` rule into two separate rules ([issue #1471](https://github.com/MarketSquare/robotframework-robocop/issues/1471)):

    ``wrong-case-in-keyword-name`` which checks case convention in keyword definition name
    ``wrong-case-in-keyword-call`` which checks case convention in keyword call name

    It allows configuring different conventions for keyword definition and keyword call names. If you have existing
    configuration for ``wrong-case-in-keyword-name`` (you are ignoring it or configuring) you need to apply the same
    config to ``wrong-case-in-keyword-call`` to retain old behaviour.

- ``SplitTooLongLine`` can now split more settings types: Library imports, Test Tags and Keyword Tags ([issue #1454](https://github.com/MarketSquare/robotframework-robocop/issues/1454))

    Example code before and after the change:

    ```robotframework
    Library    CustomLibraryWithLongerNameAndSeveralArguments    first_argument    second_argument=${longer_variable_name}    WITH NAME    name
    ```

    ```robotframework
    Library             CustomLibraryWithLongerNameAndSeveralArguments
    ...                     first_argument
    ...                     second_argument=${longer_variable_name}
    ...                 WITH NAME    name
    ```

- Restore project checkers ([issue #1108](https://github.com/MarketSquare/robotframework-robocop/issues/1108))

    Project checkers were temporarily removed in the Robocop 6.0. There are now brought back in a new form, as a separate
    command:

    ```
    robocop check-project
    ```

    This command behaves similarly to the ``check`` command, but it only runs project rules.

    The project checks itself were also refactored to be more flexible. See [project checker](https://robocop.dev/stable/linter/linter/#project-checks)
    and [custom rules project checker](https://robocop.dev/stable/linter/custom_rules/#project-checks) for reference.

- Extend robocop disablers to the whole node ([issue #1515](https://github.com/MarketSquare/robotframework-robocop/issues/1515)

    Robocop will now ignore issues in the whole node (keyword, test case, for loop, keyword call, etc.) when the disabler
    is set in the header / keyword call body. For example:

    ```robotframework
    *** Keywords ***
    My Keyword  
        FOR    ${var}    IN    1  2  3  # robocop: off=unused-variable
             Log    1
        END
        Keyword    # robocop: off=bad-indent
        ...    ${var}
        ...    ${var2}
    ```

    Previously, Robocop would ignore ``unused-variable`` only when reported on the ``FOR`` header and ``bad-indent`` only
    when reported on the same line as disabler comment. After this change, those issues will be ignored in the whole
    FOR loop and the whole ``Keyword`` call respectively.

- Ignore unused variables starting with ``_`` (``${_variable}``) ([issue #1457](https://github.com/MarketSquare/robotframework-robocop/issues/1457)

### Fixes

- Fix ``unused-variable`` and ``variable-overwritten-before-usage`` rules not reporting violations in ``TRY`` blocks ([issue #1548](https://github.com/MarketSquare/robotframework-robocop/issues/1548))
- Fix ``wrong-case-in-keyword-call`` rule false positive report on names with ``.`` character with first_word_capitalized = True ([issue #1555](https://github.com/MarketSquare/robotframework-robocop/issues/1555))
- Fix ``wrong-case-in-keyword-name`` rule incorrectly handling names with ``.`` character ([issue #1555](https://github.com/MarketSquare/robotframework-robocop/issues/1555))

### Documentation

- Added documentation linters (with MegaLinter) and fixed several issues in our documentation.

## 6.13.0

### Features

- Add ``per_file_ignores`` option to ignore rules matching file patterns ([issue #1134](https://github.com/MarketSquare/robotframework-robocop/issues/1134))

Example configuration:

```toml
[tool.robocop.lint.per_file_ignores]
"test.robot" = ["VAR02"]
"ignore_subdir/*" = ["empty-line-after-section", "DOC01"]
"ignore_file_in_subpath/test2.robot" = ["SPC10"]
```

- Allow manually disabling reports with ``enabled=False``. It can be used to disable default ``print_issues`` report ([issue #1540](https://github.com/MarketSquare/robotframework-robocop/issues/1540))
- Add ``docs_url`` property to rule class which points to rule documentation URL ([issue #1432](https://github.com/MarketSquare/robotframework-robocop/issues/1432))

### Fixes

- Fix piping output (``robocop check > output.txt``) not working on Windows because of code lines converted to emojis ([issue #1539](https://github.com/MarketSquare/robotframework-robocop/issues/1539))
- Fix configuration file loaded from the root directory with ``--ignore-file-config`` option enabled (other configuration files were correctly ignored)

### Documentation

- Describe how to extend the Robocop Rule class using ``docs_url`` as an example ([here](https://robocop.dev/stable/linter/custom_rules/#change-rule-class-behaviour)).

## 6.12.0

### Features

- Add ``extends`` configuration parameter which allows inheriting configuration from another file ([issue #1453](https://github.com/MarketSquare/robotframework-robocop/issues/1453))
- Change ``mixed-tabs-and-spaces`` (SPC06) rule behaviour to report all occurrences of mixed tabs and spaces in a file ([issue #848](https://github.com/MarketSquare/robotframework-robocop/issues/848))
-  ``format_files`` (robocop API entrypoint for formatting files) now accepts ``return_result`` parameter for returning exit code instead of raising SystemExit
- ``RenameVariables`` not longer replaces spaces in variable names with the math operators ([issue #1428](https://github.com/MarketSquare/robotframework-robocop/issues/1428))

### Fixes

- Fix ``AlignKeywordsSection`` and ``AlignTestCasesSection`` not aligning VAR variables ([issue #1493](https://github.com/MarketSquare/robotframework-robocop/issues/1493))
- Fix optional ``no-embedded-keyword-arguments`` rule fatal exception when reading a file with invalid syntax
- Fix the empty configuration file causing Robocop to fail ([issue #1536](https://github.com/MarketSquare/robotframework-robocop/issues/1536))

### Documentation

- Add ``deprecated names`` section to all the rules that list previous names and ids of the rule

## 6.11.0

### Features

- Add ``--silent`` option to disable all output when running Robocop ([issue #1512](https://github.com/MarketSquare/robotframework-robocop/issues/1512))
- Improve startup performance of the Robocop (using a Robocop repository as a benchmark: from 5s to 0.3s). It was done
  by fixing issues in handling ignored files and by properly caching configuration files (to avoid multiple lookups).
  The difference may be noticeable only for the large, complex projects ([issue #1503](https://github.com/MarketSquare/robotframework-robocop/issues/1503))

### Fixes

- Fix directories from the ``.gitignore`` file not ignored ([issue #1503](https://github.com/MarketSquare/robotframework-robocop/issues/1503))
- Fix ``migrate`` command migrating formatters with ``enabled=False`` from the old transform to select option ([issue #1492](https://github.com/MarketSquare/robotframework-robocop/issues/1492))
- Fix ``migrate`` command not splitting multiline configurations ([issue #1491](https://github.com/MarketSquare/robotframework-robocop/issues/1491))
- Fix multiline inline IF splitting. To avoid issues when formatting such code, **all inline IFs are now flattened to a single line** ([issue #1506](https://github.com/MarketSquare/robotframework-robocop/issues/1506)):

```robotframework
*** Test Cases ***
Multiline inline IF
    IF    True
    ...    Something
```

becomes:

```robotframework
*** Test Cases ***
Multiline inline IF
    IF    True    Something
```
- Fix ``enabled`` formatter parameter not validating as a boolean ([issue #1476](https://github.com/MarketSquare/robotframework-robocop/issues/1476))

### Documentation

- Mark disabled rules in the documentation (previously they were not distinguishable from the enabled rules) ([issue #1518](https://github.com/MarketSquare/robotframework-robocop/issues/1518))
- Add two new sections to the documentation:
  - [Python API Reference](https://robocop.dev/stable/user_guide/python_api/)
  - [AI integration](https://robocop.dev/stable//integrations/ai/)

## 6.10.1

### Fixes

- Fix ``verbose``, ``force_exclude`` and ``skip_gitignore`` options not supported in the configuration file

### Documentation

- Fix incorrect code examples in the documentation.

## 6.10.0

### Documentation

Release a new documentation website.

Rewrite of our documentation from Sphinx to MkDocs, now hosted at https://robocop.dev.

## 6.9.2

### Fixes

- Fix invalid Robot Framework dependency version range

## 6.9.1

### Fixes

- Fix invalid rule positions stopping Sonar Qube import ([issue #1417](https://github.com/MarketSquare/robotframework-robocop/issues/1417))
End-to-end testing of Sonar Qube issue imports revealed multiple problems with diagnostic positioning.
All problematic rules included an incorrect offset of 1. The following rules have been corrected:

- ``invalid-setting-in-resource`` (ERR16)
- ``unreachable-code`` (MISC10)
- ``keyword-name-is-reserved-word`` (NAME03)
- ``invalid-section`` (NAME16)

## 6.9.0

### Documentation

Rule documentation now contains information about deprecated names. It is especially helpful during migration to
Robocop 6.0 or comparing results between old and new Robocop reports.

## 6.8.3

### Fixes

- Fix Robocop failing to scan directory with dangling symlink ([issue #1494](https://github.com/MarketSquare/robotframework-robocop/issues/1494))

Robocop should be able to scan a directory with dangling (pointing to a non-existing path) symlink.

## 6.8.2

### Fixes

- Fix comment handling in Set Variable If with ReplaceWithVAR formatter ([issue #1495](https://github.com/MarketSquare/robotframework-robocop/issues/1495))

``ReplaceWithVAR`` no longer abruptly stops when converting ``Set Variable If`` with comments to ``VAR``.

## 6.8.1

### Fixes

- Fix Python 3.14 compatibility issues, where Robocop disabled 1/3 of the rules.

## 6.8.0

### Features

- Add a new rule: unused disabler rule ([issue #1312](https://github.com/MarketSquare/robotframework-robocop/issues/1312))

A new rule ``unused-disabler`` (MISC15) has been added to detect Robocop disabler directives (such as ``# noqa`` or
``# robocop: off``) that are not being used. This typically occurs when:

- A code violation is fixed, but the disabler is not removed
- A rule is disabled globally, making local disablers redundant
- Multiple overlapping disablers are present

- Improved comment handling in SplitTooLongLine formatter ([issue #1444](https://github.com/MarketSquare/robotframework-robocop/issues/1444))

The ``SplitTooLongLine`` formatter now has better comment handling.

**Previous behavior:**

When formatting keyword call or ``VAR`` by ``SplitTooLongLine`` formatter, comments were moved above the statement,
for example:

```
Long Keyword That Will Be Split    multiple   args  # comment
```

Was formatted to:

```
# comment
Long Keyword That Will Be Split
...    multiple
...    args
```

This caused unindented effect where robocop disabler directives (e.g. ``# robocop: off``) were also moved above the
statement and no longer applied correctly.

**New behavior:**

Comments are now kept on the first line of the split statement:

```
Long Keyword That Will Be Split  # comment
...    multiple
...    args
```

This ensures that disablers and other comments remain associated with the correct statement.

- Disablers are discoverable anywhere in comments

Disabler directives can now be placed anywhere within a comment, not just at the beginning.

**Previous behavior:**

Only the first disabler at the start of a comment was recognised:

```
# only robocop: off=some-rule is recognized
Keyword Call  # robocop: off=some-rule robocop: fmt: off

# only noqa is recognized
Keyword Call  # noqa robocop fmt: off

# nothing is recognized
Keyword Call  # TODO: robocop: off
```

**New behavior:**

All disablers are now recognised regardless of their position in the comment. Additionally, the syntax is more
flexible and rules can be separated by commas with or without spaces:

```
# Both formats are now valid:
# robocop: off=rule1,rule2
# robocop: off=rule1, rule2
```

### Fixes

- Fix overwrite mode not working from the configuration file ([issue #1478](https://github.com/MarketSquare/robotframework-robocop/issues/1478))

Fixed an issue where the ``overwrite`` mode was not being applied when specified in the configuration file. The
following configuration now works correctly:

```toml
[tool.robocop.format]
overwrite = false
```

- Fix rules url pointing to a non-existing location ([issue #1481](https://github.com/MarketSquare/robotframework-robocop/issues/1481))

Rules urls (such as SARIF helpUri, or diagnostic message urls) were pointing to non-existent locations after a
documentation refactor. URLs now correctly point to:

https://robocop.readthedocs.io/en/v{version}/rules/rules_list.html#{rule-name} .

- Fix line too long rule reporting lines with new disablers

New disabler directives (``robocop: fmt: off`` and ``fmt: off``) were not ignored by ``line-too-long`` rule.

From now on, together with other disablers, comments with disablers will be ignored when checking line length.

============================= test session starts ==============================
platform linux -- Python 3.13.3, pytest-7.4.4, pluggy-1.6.0 -- /home/quentin-sautiere/.cache/pypoetry/virtualenvs/boursa-vision-backend-lM22dsvf-py3.13/bin/python
cachedir: .pytest_cache
rootdir: /home/quentin-sautiere/Documents/workspace/python/boursa-vision/backend
configfile: pytest.ini
plugins: asyncio-0.21.2, cov-4.1.0, anyio-3.7.1
asyncio: mode=Mode.STRICT
collecting ... collected 180 items

tests/test_alerts.py::test_alerts_example PASSED                         [  0%]
tests/test_alerts.py::test_alert_model PASSED                            [  1%]
tests/test_base.py::test_base_example PASSED                             [  1%]
tests/test_base.py::test_base_model PASSED                               [  2%]
tests/test_enums.py::test_enums PASSED                                   [  2%]
tests/test_enums.py::test_enums_example PASSED                           [  3%]
tests/test_fundamental.py::test_fundamental_example PASSED               [  3%]
tests/test_instruments.py::test_instruments_example PASSED               [  4%]
tests/test_investment.py::TestInvestment::test_create_investment PASSED  [  5%]
tests/test_investment.py::TestInvestment::test_update_price_valid PASSED [  5%]
tests/test_investment.py::TestInvestment::test_update_price_wrong_currency PASSED [  6%]
tests/test_investment.py::TestInvestment::test_update_price_negative PASSED [  6%]
tests/test_investment.py::TestInvestment::test_investment_sector PASSED  [  7%]
tests/test_investment.py::TestInvestment::test_investment_type PASSED    [  7%]
tests/test_investment.py::TestInvestment::test_update_fundamental_data PASSED [  8%]
tests/test_investment.py::TestInvestment::test_update_technical_data PASSED [  8%]
tests/test_investment.py::TestInvestment::test_calculate_composite_score PASSED [  9%]
tests/test_investment.py::TestInvestment::test_assess_risk_level_medium PASSED [ 10%]
tests/test_investment.py::TestInvestment::test_is_analysis_stale_with_recent_data PASSED [ 10%]
tests/test_investment.py::TestInvestment::test_calculate_fundamental_score_with_pe_ratio PASSED [ 11%]
tests/test_investment.py::TestInvestment::test_calculate_fundamental_score_with_roe PASSED [ 11%]
tests/test_investment.py::TestInvestment::test_calculate_fundamental_score_neutral PASSED [ 12%]
tests/test_investment.py::TestInvestment::test_calculate_fundamental_score_high PASSED [ 12%]
tests/test_investment.py::TestInvestment::test_calculate_fundamental_score_low PASSED [ 13%]
tests/test_investment.py::TestFundamentalData::test_calculate_fundamental_score_excellent PASSED [ 13%]
tests/test_investment.py::TestFundamentalData::test_calculate_fundamental_score_poor PASSED [ 14%]
tests/test_investment.py::TestFundamentalData::test_calculate_fundamental_score_no_data PASSED [ 15%]
tests/test_investment.py::TestTechnicalData::test_calculate_technical_score_bullish PASSED [ 15%]
tests/test_investment.py::TestTechnicalData::test_calculate_technical_score_bearish PASSED [ 16%]
tests/test_investment.py::TestInvestmentSignalGeneration::test_generate_signal_strong_buy PASSED [ 16%]
tests/test_investment.py::TestInvestmentSignalGeneration::test_generate_signal_no_price PASSED [ 17%]
tests/test_investment.py::TestInvestmentRiskAssessment::test_assess_risk_level_high PASSED [ 17%]
tests/test_investment.py::TestInvestmentRiskAssessment::test_assess_risk_level_low PASSED [ 18%]
tests/test_investment.py::TestInvestmentRiskAssessment::test_is_analysis_stale PASSED [ 18%]
tests/test_market_data.py::test_market_data_example PASSED               [ 19%]
tests/test_market_data.py::test_update_prices PASSED                     [ 20%]
tests/test_market_data.py::test_get_typical_price PASSED                 [ 20%]
tests/test_market_data.py::test_is_gap_up PASSED                         [ 21%]
tests/test_money.py::test_currency_properties PASSED                     [ 21%]
tests/test_money.py::test_money_creation_and_rounding PASSED             [ 22%]
tests/test_money.py::test_money_addition_same_currency PASSED            [ 22%]
tests/test_money.py::test_money_addition_diff_currency_raises PASSED     [ 23%]
tests/test_money.py::test_money_subtraction PASSED                       [ 23%]
tests/test_money.py::test_money_subtraction_negative_result_raises PASSED [ 24%]
tests/test_money.py::test_money_multiplication_division PASSED           [ 25%]
tests/test_money.py::test_money_comparisons PASSED                       [ 25%]
tests/test_money.py::test_money_convert_to PASSED                        [ 26%]
tests/test_money.py::test_money_zero_and_is_zero PASSED                  [ 26%]
tests/test_money.py::test_money_from_float_and_from_string PASSED        [ 27%]
tests/test_performance.py::test_performance_example PASSED               [ 27%]
tests/test_performance.py::test_performance_creation PASSED              [ 28%]
tests/test_performance_analyzer.py::test_calculate_portfolio_performance_basic PASSED [ 28%]
tests/test_performance_analyzer.py::test_calculate_portfolio_performance_with_benchmark PASSED [ 29%]
tests/test_performance_analyzer.py::test_calculate_portfolio_performance_empty_positions PASSED [ 30%]
tests/test_performance_analyzer.py::test_calculate_position_performance_basic PASSED [ 30%]
tests/test_performance_analyzer.py::test_calculate_risk_adjusted_metrics_empty PASSED [ 31%]
tests/test_performance_analyzer.py::test_calculate_risk_adjusted_metrics_full PASSED [ 31%]
tests/test_performance_analyzer.py::test_compare_with_benchmark_empty PASSED [ 32%]
tests/test_performance_analyzer.py::test_compare_with_benchmark_full PASSED [ 32%]
tests/test_performance_analyzer.py::test_calculate_attribution_analysis PASSED [ 33%]
tests/test_performance_analyzer.py::test_suggest_rebalancing_equal_weight PASSED [ 33%]
tests/test_portfolio.py::test_portfolio_create_and_event PASSED          [ 34%]
tests/test_portfolio.py::test_add_investment_success_and_total_value PASSED [ 35%]
tests/test_portfolio.py::test_add_investment_insufficient_or_limit_exceeded[cash0-price0-3] PASSED [ 35%]
tests/test_portfolio.py::test_add_investment_insufficient_or_limit_exceeded[cash1-price1-1] PASSED [ 36%]
tests/test_portfolios.py::test_portfolios_example PASSED                 [ 36%]
tests/test_position.py::test_calculate_market_value PASSED               [ 37%]
tests/test_position.py::test_calculate_unrealized_pnl PASSED             [ 37%]
tests/test_position.py::test_calculate_return_percentage PASSED          [ 38%]
tests/test_price.py::test_price_creation_and_rounding PASSED             [ 38%]
tests/test_price.py::test_price_to_money_and_comparisons_and_format PASSED [ 39%]
tests/test_price.py::test_price_change_and_percentage PASSED             [ 40%]
tests/test_price.py::test_price_change_percentage_zero_division PASSED   [ 40%]
tests/test_price.py::test_pricepoint_and_pricedata_validations_and_properties PASSED [ 41%]
tests/test_price.py::test_price_invalid_currency_comparison PASSED       [ 41%]
tests/test_price.py::test_pricepoint_invalid_ohlc PASSED                 [ 42%]
tests/test_price.py::test_pricepoint_negative_volume PASSED              [ 42%]
tests/test_price.py::test_pricedata_chronological_and_currency PASSED    [ 43%]
tests/test_price.py::test_pricedata_slice_and_get_price_at_date PASSED   [ 43%]
tests/test_price.py::test_pricedata_average_and_lowest PASSED            [ 44%]
tests/test_price.py::test_pricedata_get_returns_short_series PASSED      [ 45%]
tests/test_price.py::test_pricedata_get_price_at_date_not_found PASSED   [ 45%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_calculate_position_risk_high_risk PASSED [ 46%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_calculate_position_risk_low_risk PASSED [ 46%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_validate_risk_limits_within_limits PASSED [ 47%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_validate_risk_limits_position_violation PASSED [ 47%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_suggest_risk_reduction PASSED [ 48%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_calculate_portfolio_risk_metrics PASSED [ 48%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_market_cap_risk_scoring PASSED [ 49%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_sector_risk_through_investment_analysis PASSED [ 50%]
tests/test_risk_calculator.py::TestRiskCalculatorService::test_technical_risk_through_investment_analysis PASSED [ 50%]
tests/test_signal.py::test_signal_action_properties PASSED               [ 51%]
tests/test_signal.py::test_confidence_score_validation_and_properties PASSED [ 51%]
tests/test_signal.py::test_signal_composite_and_validity_and_actionable PASSED [ 52%]
tests/test_signal.py::test_signal_price_target_stop_loss_validation PASSED [ 52%]
tests/test_signal.py::test_signal_to_dict_and_from_dict PASSED           [ 53%]
tests/test_signal.py::test_signal_add_metadata PASSED                    [ 53%]
tests/test_signal.py::test_signal_get_potential_return_percentage PASSED [ 54%]
tests/test_signal.py::test_signal_calculate_risk_reward_ratio PASSED     [ 55%]
tests/test_signal.py::test_confidence_score_format_and_str PASSED        [ 55%]
tests/test_signal.py::test_confidence_score_invalid_type PASSED          [ 56%]
tests/test_signal.py::test_signal_validation_errors PASSED               [ 56%]
tests/test_signal.py::test_signal_to_dict_handles_none PASSED            [ 57%]
tests/test_system.py::test_system_example PASSED                         [ 57%]
tests/test_system.py::test_system_creation PASSED                        [ 58%]
tests/test_transactions.py::test_transactions_example PASSED             [ 58%]
tests/test_transactions.py::test_transaction_creation PASSED             [ 59%]
tests/test_transactions.py::test_transaction_constraints PASSED          [ 60%]
tests/test_transactions.py::test_transaction_relations PASSED            [ 60%]
tests/test_transactions.py::test_transaction_negative_values PASSED      [ 61%]
tests/test_transactions.py::test_transaction_calculated_fields PASSED    [ 61%]
tests/test_transactions.py::test_transaction_zero_fees_and_taxes PASSED  [ 62%]
tests/test_transactions.py::test_transaction_invalid_currency PASSED     [ 62%]
tests/test_users.py::test_users_example PASSED                           [ 63%]
tests/test_yfinance_client.py::TestOptimizedYFinanceClient::test_client_initialization PASSED [ 63%]
tests/test_yfinance_client.py::TestOptimizedYFinanceClient::test_get_stock_info_success PASSED [ 64%]
tests/test_yfinance_client.py::TestOptimizedYFinanceClient::test_get_historical_data_success PASSED [ 65%]
tests/test_yfinance_client.py::TestOptimizedYFinanceClient::test_rate_limiting 

---------- coverage: platform linux, python 3.13.3-final-0 -----------
Name                                                                    Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------------------
src/__init__.py                                                             1      0   100%
src/domain/__init__.py                                                      2      0   100%
src/domain/entities/__init__.py                                            10      0   100%
src/domain/entities/base.py                                                18      0   100%
src/domain/entities/investment.py                                         230     15    93%   148, 154, 156, 163, 170, 174, 179, 193, 220, 225, 340, 357, 391-393
src/domain/entities/market_data.py                                        149     40    73%   43-54, 70-78, 138-164, 169, 172, 175, 178, 181, 184, 187, 191, 194, 197, 200, 203, 233, 239, 243-245, 249, 253-255, 259-270, 280, 288-293, 297, 301, 306, 311
src/domain/entities/portfolio.py                                          118     24    80%   219-223, 241-277, 289-297, 318-328
src/domain/entities/user.py                                               100     52    48%   35-57, 83-88, 105-115, 119-129, 133-135, 139-141, 145-148, 152, 156-158, 162, 166, 170-172, 182-193, 198, 203-204, 207, 210
src/domain/events/__init__.py                                               4      0   100%
src/domain/events/market_events.py                                         33      0   100%
src/domain/events/portfolio_events.py                                      64      0   100%
src/domain/events/user_events.py                                           26      0   100%
src/domain/repositories/__init__.py                                         4      0   100%
src/domain/repositories/base_repository.py                                 14      3    79%   28, 33, 38
src/domain/repositories/investment_repository.py                           19      5    74%   20, 25, 30, 35, 40
src/domain/repositories/market_data_repository.py                          40     11    72%   33, 46, 53, 60, 71, 76, 83, 90, 97, 108, 115
src/domain/repositories/portfolio_repository.py                            32      9    72%   29, 34, 39, 44, 49, 54, 59, 64, 69
src/domain/repositories/user_repository.py                                 30      8    73%   30, 35, 40, 45, 50, 55, 60, 67
src/domain/services/__init__.py                                             8      0   100%
src/domain/services/alert_service.py                                      102     79    23%   42, 55-71, 77-101, 110-135, 143-170, 183-210, 214-220, 230-241, 245-261
src/domain/services/performance_analyzer.py                               134     65    51%   163, 174-188, 199-213, 221-250, 255, 266-269, 273, 279-307, 312, 328, 333
src/domain/services/portfolio_allocation_service.py                       114     83    27%   56-58, 62-68, 81-95, 108-128, 141-166, 182-206, 219-262, 268-282
src/domain/services/risk_calculator.py                                    265     33    88%   175-178, 187-192, 194-195, 200-204, 250, 254-258, 311, 358, 362, 377, 383, 394, 402, 408, 410, 419, 425, 437, 474, 491, 505, 545, 557, 570, 575
src/domain/services/scoring_service.py                                     29      2    93%   60, 97
src/domain/utils/performance.py                                            15      1    93%   10
src/domain/value_objects/__init__.py                                        5      0   100%
src/domain/value_objects/alert.py                                          88     33    62%   55-56, 86-96, 100-121, 125-158, 164, 183, 203, 208-211, 214-220, 223
src/domain/value_objects/money.py                                         123     19    85%   100, 122, 132, 135, 146, 154, 171, 177, 183, 203, 207-213, 226, 230, 235, 241
src/domain/value_objects/price.py                                         168     12    93%   38, 58, 97, 136, 143, 163, 173, 178, 198, 213, 231, 277
src/domain/value_objects/signal.py                                        153     15    90%   81-82, 87-92, 127, 208, 213, 240, 257, 259, 280, 346-348, 352
src/infrastructure/__init__.py                                              2      0   100%
src/infrastructure/external/__init__.py                                     0      0   100%
src/infrastructure/external/cache_strategy.py                             198    121    39%   90-91, 95-107, 111-118, 122-131, 142-146, 150-170, 174-187, 193-211, 215-225, 229-238, 242-252, 256-269, 273-292, 296, 300-301, 305-312, 335, 340-341, 345-350, 354-355, 363-364, 381-382
src/infrastructure/external/circuit_breaker.py                             86     37    57%   84-88, 97-98, 102-104, 110-112, 118-126, 130-133, 137, 141-142, 156-158, 162-163, 174-175, 179-182, 194-195
src/infrastructure/external/client_factory.py                              86     46    47%   47, 64-68, 72-82, 86-88, 104-106, 122-127, 143-149, 165-168, 184, 197-198, 205-206, 213-214, 220, 225, 230, 235-236, 241-242
src/infrastructure/external/rate_limiter.py                                75     21    72%   44-47, 77, 87, 91-93, 112, 128-132, 136-144, 148-152, 156, 160
src/infrastructure/external/retry_strategy.py                             118     59    50%   55-56, 63, 70, 81, 95-103, 110-111, 117-124, 166-180, 197-219, 223-235, 250, 254-264, 276-283, 288-294
src/infrastructure/external/yfinance_client.py                            253    108    57%   82-84, 88-91, 133, 180-182, 203-207, 225, 230-232, 262-266, 287-291, 295-298, 319-333, 353-375, 379-396, 418-420, 428-440, 447-452, 460-472, 477, 479, 482-484, 499, 503, 507, 511-513, 517, 530, 539, 542
src/infrastructure/persistence/__init__.py                                 10      0   100%
src/infrastructure/persistence/config.py                                  132     78    41%   54-57, 80-92, 96, 116-118, 122-150, 154-159, 164, 169, 178, 185, 190-193, 200-202, 210-211, 215-216, 220, 226-238, 243-258
src/infrastructure/persistence/database.py                                 93     72    23%   40-49, 54, 69-71, 75-97, 101-109, 113-124, 136-144, 148-173, 177-245, 249-253
src/infrastructure/persistence/factory.py                                  67     31    54%   53, 57, 61, 65, 69, 73, 85, 89-90, 96, 114, 118-122, 126-130, 134-138, 142-146, 150-154
src/infrastructure/persistence/initializer.py                              81     56    31%   45-53, 66-71, 75-107, 111-116, 120-129, 134, 147-148, 153, 164-166, 174-175, 179-181, 185-186, 191-192
src/infrastructure/persistence/mappers.py                                  59     17    71%   34, 39, 47-49, 62, 83, 95, 115, 132, 157, 173, 193, 205, 237-239, 244
src/infrastructure/persistence/mappers_new.py                              76     38    50%   29, 46, 65-74, 84, 94, 111-118, 127-144, 149, 169, 184-185, 198-205
src/infrastructure/persistence/mock_repositories.py                        86     36    58%   23, 26, 30, 33, 36, 39, 42, 45, 48, 51, 54, 61, 64, 67, 70, 73, 76, 79, 82, 85, 92, 95, 99, 104, 115, 120, 125, 134, 137, 142, 147, 152, 161, 166, 169, 174
src/infrastructure/persistence/models/__init__.py                          14      0   100%
src/infrastructure/persistence/models/alerts.py                            51      0   100%
src/infrastructure/persistence/models/base.py                              12      5    58%   46, 50, 54-56
src/infrastructure/persistence/models/enums.py                             36      0   100%
src/infrastructure/persistence/models/fundamental.py                       41      0   100%
src/infrastructure/persistence/models/instruments.py                       24      0   100%
src/infrastructure/persistence/models/investment.py                        15      0   100%
src/infrastructure/persistence/models/market_data.py                       51      0   100%
src/infrastructure/persistence/models/mixins.py                            14      1    93%   57
src/infrastructure/persistence/models/performance.py                       34      0   100%
src/infrastructure/persistence/models/portfolios.py                        83     27    67%   164-170, 174, 178-181, 186-194, 231-236, 240-246
src/infrastructure/persistence/models/system.py                            29      0   100%
src/infrastructure/persistence/models/transactions.py                      25      0   100%
src/infrastructure/persistence/models/users.py                             50      2    96%   108, 112
src/infrastructure/persistence/repositories/__init__.py                     5      0   100%
src/infrastructure/persistence/repositories/investment_repository.py       37     23    38%   23-24, 28-35, 39-43, 47-51, 55-56, 60-67
src/infrastructure/persistence/repositories/market_data_repository.py      76     58    24%   25, 29-42, 52-68, 74-108, 112-140, 144-168, 172-185, 189-234
src/infrastructure/persistence/repositories/portfolio_repository.py        49     33    33%   24, 28-36, 40-45, 49-69, 73-82
src/infrastructure/persistence/repositories/user_repository.py             85     63    26%   22-23, 27-34, 38-45, 49-56, 60-64, 68-72, 76-79, 83-86, 90-92, 98-107, 111-129, 133-141
src/infrastructure/persistence/repository_factory.py                       86     44    49%   36-37, 41-42, 46-47, 55, 59-60, 64-65, 69-70, 75-88, 108-109, 113-117, 121-127, 131-137, 141, 150, 155, 161, 166, 171
src/infrastructure/persistence/sqlalchemy/database.py                     118     84    29%   37-42, 52-54, 58-98, 102-106, 111-113, 118-120, 125-133, 140, 144-208, 212-235, 239-256, 269-270, 275-277, 282-284, 290-292
src/infrastructure/persistence/unit_of_work.py                             69     34    51%   36, 41, 46, 51, 61-67, 71-77, 81-88, 92-93, 97-98, 104-109, 118, 130, 135-138
src/infrastructure/persistence/uow.py                                      72     39    46%   34-36, 41-43, 48-52, 57-61, 66-70, 74-76, 80-81, 85, 89, 93, 97, 101-105, 112, 116-117, 121, 137, 140, 143-147
src/infrastructure/web/dependencies.py                                      2      1    50%   7
src/infrastructure/web/main.py                                             19      5    74%   31, 37, 43, 49, 55
src/infrastructure/web/middleware/__init__.py                               2      0   100%
src/infrastructure/web/middleware/rate_limiting.py                          5      2    60%   8, 12
src/infrastructure/web/routers/__init__.py                                  0      0   100%
tests/conftest.py                                                          10      0   100%
tests/performance/test_database_performance.py                             92     71    23%   27-29, 33-39, 43-45, 49, 53-80, 87-102, 106-118, 122-155, 160-161, 169-175, 180
tests/performance/test_persistence_performance.py                         116     86    26%   39, 43-48, 52-57, 61-71, 86-111, 118-155, 162-199, 206-244, 249-252
tests/performance/test_persistence_performance_advanced.py                164    139    15%   35, 39-41, 45-49, 61-63, 67-86, 91-105, 110-125, 134-142, 152-184, 194-221, 226-257, 262-295, 305-335
tests/persistence/test_config.py                                           45     38    16%   16-31, 35-67
tests/persistence/test_database.py                                         18     13    28%   7-30
tests/persistence/test_factory.py                                          50     37    26%   12-25, 29-35, 39-53, 57-59
tests/persistence/test_initializer.py                                      44     26    41%   5-9, 13-16, 20-23, 37-43, 47-49, 53-54, 58-62
tests/persistence/test_mappers.py                                           5      2    60%   5-6
tests/persistence/test_mappers_new.py                                     165    157     5%   4-23, 26-38, 41-68, 71-94, 98-131, 134-179
tests/persistence/test_mock_market_data_repository.py                      19      8    58%   7, 12-14, 18-19, 23-24
tests/persistence/test_mock_portfolio_repository.py                        22     11    50%   7, 11-15, 19-21, 25-27
tests/persistence/test_mock_user_repository.py                             21     10    52%   7, 11-20, 24-25, 29-36
tests/persistence/test_persistence_imports.py                              21     14    33%   2-3, 6-7, 10-11, 14-15, 18-19, 22-23, 26-27
tests/persistence/test_repositories_minimal.py                            151     86    43%   19-20, 25, 37, 51, 56, 82-83, 94-113, 118-141, 146-175, 179-196
tests/persistence/test_uow.py                                               5      3    40%   7-9
tests/persistence/test_uow_module.py                                        3      2    33%   2-3
tests/test_alerts.py                                                        9      0   100%
tests/test_base.py                                                          8      0   100%
tests/test_enums.py                                                        10      0   100%
tests/test_fundamental.py                                                   6      0   100%
tests/test_instruments.py                                                   7      0   100%
tests/test_investment.py                                                  192      0   100%
tests/test_market_data.py                                                  25      0   100%
tests/test_money.py                                                        68      0   100%
tests/test_performance.py                                                   7      0   100%
tests/test_performance_analyzer.py                                        177     69    61%   164-167, 170-173, 176-179, 182-189, 192-195, 198-202, 205-209, 212-216, 219-226, 229-236, 239-246, 249-252, 255-264, 267-280
tests/test_portfolio.py                                                    60      0   100%
tests/test_portfolios.py                                                    6      0   100%
tests/test_position.py                                                     24      0   100%
tests/test_price.py                                                       127      0   100%
tests/test_risk_calculator.py                                              98      0   100%
tests/test_signal.py                                                      123      2    98%   69-70
tests/test_system.py                                                       12      0   100%
tests/test_transactions.py                                                111      0   100%
tests/test_users.py                                                         5      0   100%
tests/test_yfinance_client.py                                             253    165    35%   78, 97-100, 114-133, 191-197, 201-216, 220-235, 241-259, 263-286, 290-309, 313-330, 334-339, 343-365, 369-378, 382-393, 402-419, 424-453, 463-488
-----------------------------------------------------------------------------------------------------
TOTAL                                                                    6903   2589    62%


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/home/quentin-sautiere/Documents/workspace/python/boursa-vision/backend/src/infrastructure/external/yfinance_client.py:417: KeyboardInterrupt
(to show a full traceback on KeyboardInterrupt use --full-trace)
============================= 117 passed in 21.24s =============================

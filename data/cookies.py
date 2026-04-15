"""
Auto-captured Upwork session (refreshed via SeleniumBase localStorage extraction)
DO NOT EDIT - regenerate with: python refresh_session.py
Bearer token extracted from: window.localStorage or window.sessionStorage
"""

cookies = {
    "_vwo_uuid": "D9DBA5F01D298F8E761ACAF47F08E597E",
    "AWSALBTGCORS": "umMwCFtCHE0gI7pKvc8F7BlOhs3OxgP7YJquv23i5Fi1NboE6oNUZNikjYdHjw/6hMvOsITj5ABFN+wqa/yFyuHFgPTnAoG+uV6Twy8+q2XGHS3D+6YWul4WtN608u7zdVZ9MZbj/Y75AhQD3NxMqU6PS+J4Z6j9uS38RzQlfxYZ",
    "_vwo_sn": "0%3A1%3A%3A%3A%3A%3A1",
    "enabled_ff": "!CI12577UniversalSearch,!CmpLibOn,!Fluid,!MP16400Air3Migration,!SSINavUser,!i18nGA,CI17409DarkModeUI,JPAir3,OTBnrOn,SSINavUserBpa,TONB2256Air3Migration,i18nOn",
    "__cflb": "02DiuEXPXZVk436fJfSVuuwDqLqkhavJbPHAME55JKaf5",
    "_cfuvid": "YMRq6cfzKX2LKJ_T3mtVZdQdsaqZRdT73Jjt3YZ8j3A-1776271557.6866994-1.0.1.1-0xwYrG6ZpToelORN95n7F.aM_iVHk3P14o02cYHm55Y",
    "_vis_opt_s": "1%7C",
    "cookie_domain": ".upwork.com",
    "_vis_opt_test_cookie": "1",
    "AWSALBTG": "umMwCFtCHE0gI7pKvc8F7BlOhs3OxgP7YJquv23i5Fi1NboE6oNUZNikjYdHjw/6hMvOsITj5ABFN+wqa/yFyuHFgPTnAoG+uV6Twy8+q2XGHS3D+6YWul4WtN608u7zdVZ9MZbj/Y75AhQD3NxMqU6PS+J4Z6j9uS38RzQlfxYZ",
    "visitor_id": "223.123.3.123.1776271557832000",
    "visitor_gql_token": "oauth2v2_int_236060395d3d37cdcec4cfa805189ae3",
    "country_code": "PK",
    "_vwo_uuid_v2": "D9DBA5F01D298F8E761ACAF47F08E597E|b1e2453cbd6efd2fd76989a58db49f5c",
    "__cf_bm": "UKNftcZwCwoDdCPVw5mmEpbPYcjRijNuIx2Lb1GUdaA-1776271574.115243-1.0.1.1-ucxWVpR1oKhiXnln9bn0SBnssvg9LVUxmb9xGeuibhq3YO5cu.9B8rr4FbJ1OfReE4LYqZp7wno3unJoO2jnyAUs0Y7tl4ZaFLNomQOnXKlLGJGMqRSFRpxdQPmXihMW",
    "_vwo_ds": "3%241776271559%3A97.41179329%3A%3A%3A%3A%3A1776271559%3A1776271559%3A1"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer oauth2v2_int_236060395d3d37cdcec4cfa805189ae3"
}

params = {}

json_data = {
  "query": "\n  query VisitorJobSearch($requestVariables: VisitorJobSearchV1Request!) {\n    search {\n      universalSearchNuxt {\n        visitorJobSearchV1(request: $requestVariables) {\n          paging {\n            total\n            offset\n            count\n          }\n          results {\n            id\n            title\n            jobTile {\n              job {\n                id\n                ciphertext: cipherText\n                jobType\n                weeklyRetainerBudget\n                hourlyBudgetMin\n                hourlyBudgetMax\n                fixedPriceAmount {\n                  isoCurrencyCode\n                  amount\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n        ",
  "variables": {
    "requestVariables": {
      "userQuery": "web development",
      "paging": {
        "offset": 0,
        "count": 10
      }
    }
  }
}

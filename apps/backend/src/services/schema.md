# Redis 스키마

```json
// stock:005930:current_price
{
  "stck_prpr": "78000",
  "prdy_vrss": "500",
  "acml_vol": "2550032",
  "collected_at": "2025-03-19T14:05:00+09:00",
  "requested_fid_input_iscd": "005930",
  "mksc_shrn_iscd": "005930"
}

// stock:005930:current_price_fields
{
  "stck_prpr": "78000",
  "prdy_vrss": "500",
  "acml_vol": "2550032",
  "collected_at": "2025-03-19T14:05:00+09:00"
}

// stock:005930:intraday_ticks
[
  {
    "stck_cntg_hour": "140000",
    "stck_prpr": "78000",
    "cntg_vol": "1200",
    "requested_fid_input_iscd": "005930"
  },
  {
    "stck_cntg_hour": "140100",
    "stck_prpr": "78100",
    "cntg_vol": "800",
    "requested_fid_input_iscd": "005930"
  }
]```

```

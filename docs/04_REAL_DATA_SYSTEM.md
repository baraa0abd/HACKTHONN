# Layl real-data system

The primary system queries World Bank Space2Stats resource `DR0095685`, the Annual ADM2 Nighttime Lights table derived from NASA Black Marble and aggregated using World Bank official second-level administrative boundaries. The exact filter is `ISO_A3='IRQ'`.

The pinned response contains 1,313 district-year records: 101 Iraqi districts with a complete 13-year sequence from 2012 through 2024. The fetcher also stores the published schema, request URL, UTC retrieval time, and SHA-256 hashes. The runner refuses modified inputs.

Layl uses `ntl_nogf_5km_mean`, the annual mean radiance after excluding pixels within five kilometres of mapped gas-flaring locations. For each district it reports latest radiance, first-to-latest percentage change, and the least-squares trend in `log1p(radiance)`. It separately ranks the lowest-radiance districts whose latest good-quality share is at least 90%, and districts with the fastest brightening trends.

The input records and returned metrics are real. The ranking is an area-screening result rather than an observatory approval: Black Marble measures upward radiance, while astronomy also depends on zenith sky brightness, spectral composition, atmosphere, Moon, horizon, elevation, access, and security. The next evidence gate is calibrated SQM measurement at candidate locations, not a synthetic model.

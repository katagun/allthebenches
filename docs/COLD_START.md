# Cold-start performance

The comparison uses `data/comparison.json`, generated from the same reviewed dataset as the downloadable archival snapshots. The HTML preloads it while JavaScript is downloading, and includes a small initial navigation/loading shell.

The comparison payload includes every display cell and configuration, market data, and the observation/series fields needed for filtering. It omits full observation evidence, duplicate observation arrays, and saturation evidence records. Setup values are reduced to known/unknown markers only in this internal filter index; every key and unknown marker is retained to preserve completeness filtering. Full original setup values remain in the evidence archive and downloadable data.

Full provenance is fetched on demand for score/model panels, detail pages, coverage pages, and CSV export. Its filename includes its content hash, so an open comparison cannot silently mix evidence from a newer snapshot. Requests and successful parsed snapshots are shared across mounts and navigation. Failed requests are evicted so retry works. The row worker and bounded table rendering remain in place.

## Regression checks

- Snapshot tests compare every preset and evidence-sensitive filter against the full archival data.
- Browser tests require the matrix to render without fetching full evidence or the legacy results archive, then verify evidence is available when a score is opened.
- The existing pre-commit and CI bundle check caps comparison startup at 450 KiB gzip and 9 MiB decoded. Raising these limits should require another cold-start profile.
- Mobile contrast tests cover light, explicit dark, and system dark themes in resting, hover, and keyboard-focus states.

## Measurement, October 18, 2026

Controlled local production builds, identical gzip server, fresh Chromium context/cache disabled, 390×844 viewport, 80 ms latency, 500,000 bytes/s download, 4× CPU slowdown:

| Metric | Before | After |
| --- | ---: | ---: |
| First contentful paint | 840 ms | 304 ms |
| First mobile result card | 5,771 ms | 1,824 ms |
| Initial data, gzip | 1,578,178 bytes | 399,969 bytes |
| Initial data, decoded | 28,369,269 bytes | 8,790,635 bytes |

These are single controlled measurements, not field percentiles or promises for every device. A separate live-site baseline took 19.6 seconds under the same throttle; CDN/network variability makes it unsuitable as the before/after comparison.

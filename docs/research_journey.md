# Research Journey integration

Source: supplied 313-page Colab PDF, SHA-256 stored in runtime manifest. All pages indexed as text/image inventory. Original graph code and output at pages 285-297 identifies 19 unique embedded figures, in order; duplicate clipped image occurrences across notebook pages were deduplicated by PDF xref. Exact embedded image bytes preserved with per-file SHA-256. No twentieth graph reconstructed. Page 283/284 archived 12-seed SAGE V3 summary and BF reliability now resolve the prior source gap. Old 410-page and current 313-page exports remain distinct references.

GA-Fuzzy simplified model rates/CI appear only in supplied brief; not verified from the current PDF's completed outputs. The final PDF code stops during GA setup. Pending-source labels retained, no fabricated graph. NS-3 and simplified model results never merged. No original model retraining, CSV prediction reconstruction or new simulation performed.

New runtime module journey.py reads data/research/journey. Routes provide authenticated manifest, whitelisted original PNG/PDF assets, bounded selected-figure PDF ZIP export and escaped A4 print HTML. No new runtime dependencies: reportlab/PyMuPDF used only for release asset authoring; PDFs prebuilt offline. Original app routes retained.

Journey.tsx provides eight stages, four source-labelled findings, 19 thumbnail graph viewer with zoom/previous/next, original-page provenance, selected export, ten-slide fullscreen presentation, notes and report controls. 30-page fixed A4 PDF includes cover, architecture, eight stages, conclusion and 19 original graph pages. Graphs-only PDF and 19 single-figure PDFs are included. Browser print HTML offers actual Print/Save dialog; fixed PDF is available if browser printing is unsupported.

Assets prepared with work/extract_journey.py and work/build_journey_report.py from workspace root. Tests: python -m pytest tests -q. Frontend: npm --prefix frontend run build. Runtime: python -m orbit --lan or Orbit.exe. Do not expose arbitrary filesystem paths through asset routes.

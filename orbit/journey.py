"""Read-only archived research assets; no reconstructed experiment predictions."""

import io
import json
import zipfile
from html import escape

from fastapi import Query
from fastapi.responses import FileResponse, HTMLResponse, Response


def install(app, ctx):
    root = ctx["data"] / "research" / "journey"

    def manifest():
        p = root / "manifest.json"
        if not p.is_file():
            raise ValueError("Install the research assets from the complete update package.")
        return json.loads(p.read_text())

    def chosen(ids):
        m = manifest()
        values = [int(v) for v in ids.split(",")] if ids else [g["id"] for g in m["graphs"]]
        if (
            not values
            or len(values) > 19
            or len(set(values)) != len(values)
            or any(v < 1 or v > 19 for v in values)
        ):
            raise ValueError("Select 1–19 different original figures.")
        return [m["graphs"][v - 1] for v in values]

    @app.get("/api/journey")
    def index():
        return manifest()

    @app.get("/api/journey/file/{name}")
    def asset(name: str, download: bool = False):
        valid = (
            {g["file"] for g in manifest()["graphs"]}
            | {"original.pdf", "report.pdf", "graphs.pdf"}
            | {f"graph-{i:02d}.pdf" for i in range(1, 20)}
        )
        if name not in valid or not (root / name).is_file():
            raise ValueError("Choose an available research asset.")
        return FileResponse(
            root / name,
            filename=name if download else None,
            media_type="application/pdf" if name.endswith(".pdf") else "image/png",
        )

    @app.get("/api/journey/selected")
    def selected(ids: str = Query(..., max_length=80)):
        graphs = chosen(ids)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for g in graphs:
                z.write(root / f"graph-{g['id']:02d}.pdf", f"Figure-{g['id']:02d}.pdf")
            z.writestr("provenance.json", json.dumps(graphs, indent=2))
        return Response(
            buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="Orbit-selected-figures.zip"'},
        )

    @app.get("/api/journey/print.js")
    def print_script():
        return Response(
            "document.querySelector('button').addEventListener('click',()=>window.print());",
            media_type="application/javascript",
        )

    @app.get("/api/journey/print")
    def print_view(ids: str = Query("", max_length=80), report: bool = False):
        m = manifest()
        parts = [
            "<!doctype html><html><head><title>ORBIT Research Print</title><style>@page{size:A4;margin:18mm}body{font:12pt Arial;color:#172b40;margin:24px}section{break-after:page;page-break-after:always}img{width:100%;height:auto;max-height:190mm;object-fit:contain;break-inside:avoid}figure{break-inside:avoid;margin:0}small{font-size:9pt}h1{font-size:24pt}@media print{button{display:none}body{margin:0}}</style></head><body><button>Print / Save as PDF</button>"
        ]
        if report:
            parts.append(
                "<section><h1>ORBIT Research Report</h1><p>Archived research, successes, failures and limitations.</p><p>"
                + escape(m["missing"])
                + "</p></section>"
            )
            for s in m["stages"]:
                parts.append(
                    "<section><h1>"
                    + escape(s["title"])
                    + "</h1><p>"
                    + escape(s["text"])
                    + "</p></section>"
                )
        for g in chosen(ids):
            parts.append(
                "<section><h1>Figure "
                + str(g["id"])
                + ": "
                + escape(g["title"])
                + '</h1><figure><img src="/api/journey/file/'
                + g["file"]
                + '"><figcaption>'
                + escape(g["caption"])
                + "</figcaption></figure><p>"
                + escape(g["kind"] + " | " + g["status"])
                + "</p><small>Original source pages "
                + escape(str(g["source_pages"]))
                + "; no new experiments. Figure "
                + str(g["id"])
                + " of 19.</small></section>"
            )
        return HTMLResponse(
            "".join(parts) + '<script src="/api/journey/print.js"></script></body></html>'
        )

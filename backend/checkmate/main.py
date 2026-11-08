from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .contracts import ExplanationRequest, ExplanationResponse, Status
from .service import ExplanationService
from .generation import configured_service


def create_app(service: ExplanationService | None = None) -> FastAPI:
    service = service or ExplanationService()
    app = FastAPI(title="CHECKMATE Manual API", version="1.0.0")

    @app.get("/health")
    def health():
        embed = getattr(service.ranker, "embed", None)
        return {"status": "ok", "generationMode": service.mode, "indexVersion": service.catalog.indexVersion,
                "retrievalMode": service.ranker.name, "embeddingNumGpu": getattr(embed, "num_gpu", None)}

    @app.get("/v1/manual-profiles")
    def profiles():
        return {"profiles": [p.model_dump() for p in service.catalog.profiles], "indexVersion": service.catalog.indexVersion}

    @app.post("/v1/explanations", response_model=ExplanationResponse)
    def explanations(request: ExplanationRequest):
        result = service.explain(request)
        if result.status == Status.TEMPORARILY_UNAVAILABLE:
            return JSONResponse(status_code=503, content=result.model_dump(mode="json"))
        return result

    return app


load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
app = create_app(configured_service())

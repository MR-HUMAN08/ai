try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv is required. Run: uv sync") from e

try:
    from ..models import RedTeamAction, RedTeamObservation
    from .environment import RedTeamPentestEnvironment
except ImportError:
    from models import RedTeamAction, RedTeamObservation
    from server.environment import RedTeamPentestEnvironment

app = create_app(
    RedTeamPentestEnvironment,
    RedTeamAction,
    RedTeamObservation,
    env_name="redteampentestlab",

    max_concurrent_envs=1,
)

def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()

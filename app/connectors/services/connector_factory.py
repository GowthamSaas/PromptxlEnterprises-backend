from fastapi import HTTPException

from app.connectors.models import ConnectorProvider

from app.connectors.services.vercel_service import (
    vercel_service
)

from app.connectors.services.supabase_service import (
    supabase_service
)

from app.connectors.services.github_service import (
    github_service
)


class ConnectorFactory:

    @staticmethod
    def get_service(provider: ConnectorProvider):

        # ------------------------------------
        # Vercel
        # ------------------------------------

        if provider == ConnectorProvider.VERCEL:
            return vercel_service

        # ------------------------------------
        # GitHub
        # ------------------------------------

        if provider == ConnectorProvider.GITHUB:
            return github_service

        # ------------------------------------
        # Supabase
        # ------------------------------------

        if provider == ConnectorProvider.SUPABASE:
            return supabase_service

        # ------------------------------------
        # Unknown Provider
        # ------------------------------------

        raise HTTPException(
            status_code=400,
            detail=f"{provider.value} connector is not supported."
        )
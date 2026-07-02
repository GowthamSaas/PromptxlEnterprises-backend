__all__ = ["router"]


def router():
    from .router import router as router_instance

    return router_instance

class RecursoNoEncontradoError(Exception):
    """Excepción de dominio cuando un recurso (ej. Producto) no existe. Se mapea a HTTP 404."""
    pass

class ConflictoInventarioError(Exception):
    """Excepción de dominio cuando no hay stock suficiente. Se mapea a HTTP 409."""
    pass

from extensions import db


class Cliente(db.Model):
    __tablename__ = "cliente"

    idCliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idPersona = db.Column(
        db.Integer, db.ForeignKey("persona.idPersona"), nullable=False
    )
    idUsuario = db.Column(  # <-- Clave foránea en Cliente
        db.Integer, db.ForeignKey("usuario.idUsuario"), nullable=False
    )

    # Relación con Persona
    persona = db.relationship(
        "Persona", backref=db.backref("clientes_relacionados", lazy=True)
    )

    # Relación con Usuario:
    # 1. Crea la propiedad 'usuario' en Cliente.
    # 2. Usa backref para crear la colección 'clientes' en Usuario.
    usuario = db.relationship(
        "Usuario", backref=db.backref("clientes", lazy=True)  # <-- CORREGIDO
    )

    def __repr__(self):
        return f"<Cliente {self.idCliente}>"

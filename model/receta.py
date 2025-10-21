from extensions import db


class Receta(db.Model):
    __tablename__ = "receta"

    idReceta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombreReceta = db.Column(db.String(50), nullable=False)
    ingredientes = db.Column(db.JSON, nullable=False)
    Descripccion = db.Column(db.Text)
    estatus = db.Column(db.Integer, default=1)
    cantidad_galletas = db.Column(db.Integer, nullable=False)
    imagen_galleta = db.Column(db.String(100), default="default.png")

    # Relación hacia Galleta
    galletas_rel = db.relationship("Galleta", back_populates="receta", lazy=True)

    def __repr__(self):
        return f"<Receta {self.nombreReceta}>"

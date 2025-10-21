from extensions import db


class Galleta(db.Model):
    __tablename__ = "galletas"

    id_galleta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_galleta_id = db.Column(
        db.Integer, db.ForeignKey("tipo_galleta.id_tipo_galleta"), nullable=False
    )
    galleta = db.Column(db.String(100), nullable=False)
    existencia = db.Column(db.Integer, nullable=False)
    receta_id = db.Column(db.Integer, db.ForeignKey("receta.idReceta"), nullable=False)

    receta = db.relationship("Receta", back_populates="galletas_rel")
    tipo = db.relationship(
        "TipoGalleta", back_populates="galletas", overlaps="tipo_galleta"
    )
    # referencia por string rompe la circularidad
    lotes = db.relationship("LoteGalletas", back_populates="galleta", lazy=True)

    def __repr__(self):
        return f"<Galleta {self.galleta}>"

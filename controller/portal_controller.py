from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
)
from datetime import datetime, timedelta
from model.tipo_galleta import db, TipoGalleta
from model.galleta import db, Galleta
from model.orden import db, Orden
from model.detalle_venta_orden import DetalleVentaOrden
from model.cliente import db, Cliente
from sqlalchemy.orm import joinedload
import json

portal_cliente_bp = Blueprint(
    "portal_cliente", __name__, url_prefix="/portal", template_folder="view"
)

# ID del cliente por defecto
CLIENTE_PRUEBA_ID = 1


# ---------------------------
# Funciones de carrito
# ---------------------------
def get_cliente_carrito(cliente_id):
    carrito_cookie = request.cookies.get(f"carrito_{cliente_id}")
    return json.loads(carrito_cookie) if carrito_cookie else []


def set_cliente_carrito(cliente_id, carrito):
    response = make_response(redirect(url_for("portal_cliente.portal_cliente")))
    response.set_cookie(
        f"carrito_{cliente_id}",
        json.dumps(carrito),
        max_age=30 * 24 * 60 * 60,  # 30 días
        httponly=True,
        secure=False,  # ⚠ True si usas HTTPS
        samesite="Lax",
    )
    return response


def agregar_al_carrito(cliente_id):
    galleta_id = request.form.get("galleta_id")
    cantidad = int(request.form.get("cantidad", 1))

    if not galleta_id:
        flash("Debe seleccionar una galleta", "error")
        return redirect(url_for("portal_cliente.portal_cliente"))

    galleta = Galleta.query.get(galleta_id)
    if galleta:
        if cantidad > galleta.existencia:
            flash(
                f"No hay suficiente existencia. Disponibles: {galleta.existencia}",
                "error",
            )
            return redirect(url_for("portal_cliente.portal_cliente"))

        carrito = get_cliente_carrito(cliente_id)

        item_existente = next(
            (item for item in carrito if item["galleta_id"] == int(galleta_id)), None
        )

        if item_existente:
            nueva_cantidad = item_existente["cantidad"] + cantidad
            if nueva_cantidad > galleta.existencia:
                flash(
                    f"No hay suficiente existencia. Disponibles: {galleta.existencia}",
                    "error",
                )
                return redirect(url_for("portal_cliente.portal_cliente"))

            item_existente["cantidad"] = nueva_cantidad
            item_existente["subtotal"] = (
                float(galleta.tipo_galleta.costo) * nueva_cantidad
            )
        else:
            carrito.append(
                {
                    "galleta_id": galleta.id_galleta,
                    "nombre": galleta.galleta,
                    "tipo": galleta.tipo_galleta.nombre,
                    "precio": float(galleta.tipo_galleta.costo),
                    "cantidad": cantidad,
                    "subtotal": float(galleta.tipo_galleta.costo) * cantidad,
                }
            )

        response = set_cliente_carrito(cliente_id, carrito)
        flash("Producto agregado al carrito", "success")
        return response

    return redirect(url_for("portal_cliente.portal_cliente"))


def eliminar_del_carrito(cliente_id):
    galleta_id = int(request.form.get("galleta_id"))
    carrito = get_cliente_carrito(cliente_id)
    nuevo_carrito = [item for item in carrito if item["galleta_id"] != galleta_id]
    response = set_cliente_carrito(cliente_id, nuevo_carrito)
    flash("Producto eliminado del carrito", "info")
    return response


def limpiar_carrito(cliente_id):
    response = make_response(redirect(url_for("portal_cliente.portal_cliente")))
    response.set_cookie(f"carrito_{cliente_id}", "", expires=0)
    flash("Carrito vaciado", "info")
    return response


# ---------------------------
# Cliente fijo
# ---------------------------
def obtener_cliente_actual():
    """Carga el cliente con la relación persona ya disponible."""
    cliente = (
        Cliente.query.options(joinedload(Cliente.persona))
        .filter_by(idCliente=CLIENTE_PRUEBA_ID)
        .first()
    )
    if cliente:
        db.session.add(cliente)  # asegura que esté en la sesión activa
    return cliente


# ---------------------------
# Rutas
# ---------------------------
@portal_cliente_bp.route("/")
def index():
    cliente = obtener_cliente_actual()
    nombre_completo = (
        f"{cliente.persona.nombre} {cliente.persona.apPaterno}"
        if cliente and cliente.persona
        else "Cliente Demo"
    )
    return render_template("portal/welcome.html", nombre_completo=nombre_completo)


@portal_cliente_bp.route("/portal-cliente", methods=["GET", "POST"])
def portal_cliente():
    cliente = obtener_cliente_actual()
    if not cliente:
        flash("No se encontró el cliente por defecto", "error")
        return redirect(url_for("portal_cliente.index"))

    carrito = get_cliente_carrito(cliente.idCliente)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "agregar":
            return agregar_al_carrito(cliente.idCliente)
        elif action == "eliminar":
            return eliminar_del_carrito(cliente.idCliente)
        elif action == "limpiar":
            return limpiar_carrito(cliente.idCliente)

    tipos_galletas = TipoGalleta.query.all()
    tipo_seleccionado = request.args.get("tipo_galleta")

    galletas_query = Galleta.query.options(joinedload(Galleta.tipo_galleta))
    if tipo_seleccionado:
        galletas_query = galletas_query.filter_by(tipo_galleta_id=tipo_seleccionado)
    galletas = galletas_query.all()

    total = sum(item["subtotal"] for item in carrito)

    nombre_completo = (
        f"{cliente.persona.nombre} {cliente.persona.apPaterno}"
        if cliente and cliente.persona
        else "Cliente Demo"
    )

    return render_template(
        "portal/portal_cliente.html",
        tipos_galletas=tipos_galletas,
        galletas=galletas,
        carrito=carrito,
        total=total,
        nombre_completo=nombre_completo,
    )


@portal_cliente_bp.route("/confirmar-pedido", methods=["POST"])
def confirmar_pedido():
    cliente = obtener_cliente_actual()
    if not cliente:
        flash("No se encontró el cliente por defecto", "error")
        return redirect(url_for("portal_cliente.portal_cliente"))

    carrito = get_cliente_carrito(cliente.idCliente)
    if not carrito:
        flash("No hay productos en el carrito", "error")
        return redirect(url_for("portal_cliente.portal_cliente"))

    try:
        for item in carrito:
            galleta = Galleta.query.get(item["galleta_id"])
            if not galleta or item["cantidad"] > galleta.existencia:
                flash(
                    f'No hay suficiente existencia de {item["nombre"]}. Disponibles: {galleta.existencia if galleta else 0}',
                    "error",
                )
                return redirect(url_for("portal_cliente.portal_cliente"))

        nueva_orden = Orden(
            descripcion="Pedido de galletas",
            total=sum(item["subtotal"] for item in carrito),
            fechaAlta=datetime.now(),
            fechaEntrega=datetime.now() + timedelta(days=3),
            tipoVenta="Portal Cliente",
            cliente_id=cliente.idCliente,
        )
        db.session.add(nueva_orden)
        db.session.flush()

        for item in carrito:
            detalle = DetalleVentaOrden(
                galletas_id=item["galleta_id"],
                cantidad=item["cantidad"],
                subtotal=item["subtotal"],
                orden_id=nueva_orden.id_orden,
            )
            db.session.add(detalle)
            galleta = Galleta.query.get(item["galleta_id"])
            galleta.existencia -= item["cantidad"]

        db.session.commit()

        response = make_response(redirect(url_for("portal_cliente.portal_cliente")))
        response.set_cookie(f"carrito_{cliente.idCliente}", "", expires=0)
        flash(
            f"Pedido confirmado con éxito! Número de orden: {nueva_orden.id_orden}",
            "success",
        )
        return response

    except Exception as e:
        db.session.rollback()
        flash(f"Error al confirmar el pedido: {str(e)}", "error")
        return redirect(url_for("portal_cliente.portal_cliente"))


@portal_cliente_bp.route("/mis-pedidos")
def mis_pedidos():
    cliente = obtener_cliente_actual()
    if not cliente:
        flash("No se encontró el cliente por defecto", "error")
        return redirect(url_for("portal_cliente.portal_cliente"))

    ordenes = (
        Orden.query.filter_by(cliente_id=cliente.idCliente)
        .order_by(Orden.fechaAlta.desc())
        .all()
    )

    pedidos = []
    for orden in ordenes:
        pedido = {
            "id": orden.id_orden,
            "fecha": orden.fechaAlta.strftime("%d/%m/%Y %H:%M"),
            "entrega": orden.fechaEntrega.strftime("%d/%m/%Y"),
            "total": f"${orden.total:.2f}",
            "detalles": [],
        }
        for detalle in orden.detalles:
            galleta = detalle.galletas
            pedido["detalles"].append(
                {
                    "nombre": galleta.galleta,
                    "tipo": galleta.tipo_galleta.nombre,
                    "cantidad": detalle.cantidad,
                    "subtotal": f"${detalle.subtotal:.2f}",
                }
            )
        pedidos.append(pedido)

    nombre_completo = (
        f"{cliente.persona.nombre} {cliente.persona.apPaterno}"
        if cliente and cliente.persona
        else "Cliente Demo"
    )

    return render_template(
        "portal/mis_pedidos.html", pedidos=pedidos, nombre_completo=nombre_completo
    )

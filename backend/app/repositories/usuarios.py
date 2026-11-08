from app.domain.enums import RolSesion

USUARIOS_SOPORTE = {
    "soporte1": "pbkdf2_sha256$600000$7374033d63e09e23ecb42a5133cc06de$3e640298306e4eb90ad9e9d7ae8b3ad33df2800362106fa35ee697a4aa545a3d",
    "soporte2": "pbkdf2_sha256$600000$6f2fb89a1ddf18c8dd0dc0b48450e1dc$8ae072dc95c5be5f7291b59072a1215e2cb6e640c88f76879d339e004617c9e3",
    "soporte3": "pbkdf2_sha256$600000$cbfab0dc8694d3f0a8ed4f3c2c29617c$337281ddfead88fbe8208482c2c9fa442bfbb5581e2f1ca4e2e21142d263dade",
    "soporte4": "pbkdf2_sha256$600000$895f8d97db79d6023d7a0790250da442$693ebd66bf087fe7de44a012fc9f76a1986d311e79244a14a6c485210011d266",
}

USUARIOS_CLIENTE = {
    "asa_promotions": "pbkdf2_sha256$600000$cfc297bc2c4aec06de4a6e912e66b99e$832cc094203f1a78e70f6da9505a28a61918ae59190cd62409e3db98f7f192b2",
    "arceyut_producciones": "pbkdf2_sha256$600000$9afe3b0b66c3350d10a89190b1d00e6d$cad1f547292b6adf4a281f6ca09bf02aa5aa71e856f41f8ea2a993c2fd3e820b",
    "show_business_guatemala": "pbkdf2_sha256$600000$9f87c59143b2aaae35fd2a30d9188ba4$b7e97e2f00d2da25c6558064487c199d7af464ad54eca890940e00bec1618acc",
    "promotora_2_mundos": "pbkdf2_sha256$600000$db1a8cfae93c104e29bd2af27f71295c$2643020f9e3988b1caff06e29bd0d917faab8c12685b879bab8b18a43cae221e",
    "epica_eventos": "pbkdf2_sha256$600000$b52ff14e61f308a225002311e33bc2ff$e39b03bcc54279a786f4668fffe885ad3cfb6f041cf314f0443e6bd58bb5c735",
}


def obtener_hash_contrasena(usuario: str) -> str | None:
    return USUARIOS_SOPORTE.get(usuario) or USUARIOS_CLIENTE.get(usuario)


def obtener_rol(usuario: str) -> RolSesion | None:
    if usuario in USUARIOS_SOPORTE:
        return RolSesion.agente
    if usuario in USUARIOS_CLIENTE:
        return RolSesion.cliente
    return None

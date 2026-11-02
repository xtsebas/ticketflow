USUARIOS_SOPORTE = {
    "soporte1": "pbkdf2_sha256$600000$7374033d63e09e23ecb42a5133cc06de$3e640298306e4eb90ad9e9d7ae8b3ad33df2800362106fa35ee697a4aa545a3d",
    "soporte2": "pbkdf2_sha256$600000$6f2fb89a1ddf18c8dd0dc0b48450e1dc$8ae072dc95c5be5f7291b59072a1215e2cb6e640c88f76879d339e004617c9e3",
    "soporte3": "pbkdf2_sha256$600000$cbfab0dc8694d3f0a8ed4f3c2c29617c$337281ddfead88fbe8208482c2c9fa442bfbb5581e2f1ca4e2e21142d263dade",
    "soporte4": "pbkdf2_sha256$600000$895f8d97db79d6023d7a0790250da442$693ebd66bf087fe7de44a012fc9f76a1986d311e79244a14a6c485210011d266",
}


def obtener_hash_contrasena(usuario: str) -> str | None:
    return USUARIOS_SOPORTE.get(usuario)

// Valores del dominio. Deben coincidir con backend/app/domain/enums.py y con la Fase 1.

export const ESTADOS = [
  { valor: 'abierto', etiqueta: 'Abierto' },
  { valor: 'en_progreso', etiqueta: 'En progreso' },
  { valor: 'resuelto', etiqueta: 'Resuelto' },
  { valor: 'cerrado', etiqueta: 'Cerrado' },
]

// Mismas transiciones que TRANSICIONES_ESTADO en backend/app/services/tickets.py
export const TRANSICIONES = {
  abierto: ['en_progreso'],
  en_progreso: ['resuelto'],
  resuelto: ['cerrado', 'en_progreso'],
  cerrado: [],
}

export const ACCION_TRANSICION = {
  'abierto>en_progreso': 'Comenzar a atender',
  'en_progreso>resuelto': 'Marcar como resuelto',
  'resuelto>cerrado': 'Cerrar ticket',
  'resuelto>en_progreso': 'Reabrir',
}

// Ventanas SLA (Fase 1, sección 6 y README raíz)
export const PRIORIDADES = [
  { valor: 'P1', etiqueta: 'P1 · Crítico', respuesta: '15 min', resolucion: '2 h' },
  { valor: 'P2', etiqueta: 'P2 · Alto', respuesta: '30 min', resolucion: '4 h' },
  { valor: 'P3', etiqueta: 'P3 · Medio', respuesta: '1 h', resolucion: '8 h' },
  { valor: 'P4', etiqueta: 'P4 · Bajo', respuesta: '4 h', resolucion: '1 día hábil' },
]

// Niveles de atención (Fase 1, sección 4)
export const NIVELES = [
  {
    valor: 'N1',
    etiqueta: 'N1 · Soporte al cliente',
    ayuda: 'Consultas de compra, reembolsos, reenvío de tickets y dudas generales de organizadores',
  },
  {
    valor: 'N2',
    etiqueta: 'N2 · Soporte técnico de plataforma',
    ayuda: 'Fallas de validación de QR, sincronización del panel de ventas y problemas de la app',
  },
  {
    valor: 'N3',
    etiqueta: 'N3 · Ingeniería de pagos e integraciones',
    ayuda: 'Fallas de la pasarela de pago, facturación FEL, seguridad o cifrado de datos',
  },
]

// Escalamiento jerárquico (Fase 1, matriz de escalamiento)
export const ESCALAMIENTOS = [
  {
    valor: 'gerente_operaciones',
    etiqueta: 'Gerente de Operaciones',
    ayuda: 'Evento masivo en curso con riesgo de imagen pública o pérdida financiera significativa',
  },
  {
    valor: 'direccion_comercial',
    etiqueta: 'Dirección comercial / Patrocinador',
    ayuda: 'El organizador exige compensación fuera de política o amenaza con cancelar el contrato',
  },
]

// Criterios de impacto y urgencia (Fase 1, sección 6)
export const IMPACTOS = [
  {
    valor: 'alto',
    etiqueta: 'Alto',
    ayuda: 'Más de 100 usuarios, un evento en curso, más del 30 % de las operaciones, o impide el ingreso, pago o venta',
  },
  {
    valor: 'medio',
    etiqueta: 'Medio',
    ayuda: 'Entre 10 y 100 usuarios, un solo organizador o 10–30 % de las operaciones; hay alternativa temporal',
  },
  {
    valor: 'bajo',
    etiqueta: 'Bajo',
    ayuda: 'Menos de 10 usuarios o una función secundaria, sin detener ventas, validaciones ni acceso',
  },
]

export const URGENCIAS = [
  {
    valor: 'alta',
    etiqueta: 'Alta',
    ayuda: 'Ocurre durante un evento activo o una venta crítica; debe atenderse en menos de 30 min',
  },
  {
    valor: 'media',
    etiqueta: 'Media',
    ayuda: 'Puede tolerarse entre 30 min y 4 h, pero requiere atención el mismo día',
  },
  {
    valor: 'baja',
    etiqueta: 'Baja',
    ayuda: 'Puede esperar más de 4 h o hasta el siguiente día hábil sin consecuencias relevantes',
  },
]

// Matriz impacto × urgencia, igual que backend/app/services/prioridad.py
const MATRIZ = {
  alto: { alta: 'P1', media: 'P2', baja: 'P3' },
  medio: { alta: 'P2', media: 'P3', baja: 'P4' },
  bajo: { alta: 'P3', media: 'P4', baja: 'P4' },
}

export function calcularPrioridad(impacto, urgencia) {
  return MATRIZ[impacto]?.[urgencia] ?? null
}

// Impacto, urgencia y nivel sugeridos para cada servicio del catálogo (Fase 1).
// - Pagos y validación de QR son el núcleo de la garantía del servicio (pago < 2 min, QR válido):
//   impiden ingreso o pago, por eso impacto alto.
// - nivel: a quién corresponde según "Niveles de atención". El ticket siempre entra en N1 y el
//   panel de soporte sugiere escalar cuando el caso pertenece a N2 o N3.
// El usuario puede cambiar impacto y urgencia antes de enviar.
export const SUGERENCIA_POR_CATEGORIA = {
  qr_rechazado_en_puerta: { impacto: 'alto', urgencia: 'alta', nivel: 'N2' },
  pago_no_procesado_cobro_duplicado: { impacto: 'alto', urgencia: 'alta', nivel: 'N3' },
  panel_ventas_desincronizado: { impacto: 'alto', urgencia: 'media', nivel: 'N2' },
  correo_confirmacion_no_entregado: { impacto: 'medio', urgencia: 'media', nivel: 'N1' },
  creacion_publicacion_evento: { impacto: 'medio', urgencia: 'baja', nivel: 'N1' },
  cambio_asiento_categoria_entrada: { impacto: 'bajo', urgencia: 'media', nivel: 'N1' },
  reenvio_ticket_digital: { impacto: 'bajo', urgencia: 'media', nivel: 'N1' },
  reembolso_cancelacion_entrada: { impacto: 'bajo', urgencia: 'baja', nivel: 'N1' },
}

// OLA de atención de incidentes críticos (Fase 1, sección 7): un P1 se escala a N2 en ≤ 10 min.
export const OLA_ESCALAMIENTO_P1_MIN = 10

// Horario de atención (Fase 1, sección 4)
export const HORARIO =
  'Lun–Vie 08:00–18:00 (soporte estándar). Incidentes críticos de pago y validación en puerta: Vie–Dom hasta el cierre del último evento del día.'

export const TIPOS = [
  { valor: 'incidente', etiqueta: 'Incidente', ayuda: 'Algo dejó de funcionar como debería' },
  { valor: 'solicitud', etiqueta: 'Solicitud', ayuda: 'Necesito que el equipo haga algo por mí' },
]

export function etiqueta(lista, valor) {
  return lista.find((x) => x.valor === valor)?.etiqueta ?? valor
}
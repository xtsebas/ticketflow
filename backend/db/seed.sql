insert into categorias (slug, nombre, tipo, descripcion, quien_reporta) values
  ('reenvio_ticket_digital', 'Reenvío de ticket digital', 'solicitud', 'El usuario no localiza o eliminó el correo con su código QR y pide que se lo reenvíen', 'Usuario/asistente'),
  ('reembolso_cancelacion_entrada', 'Reembolso o cancelación de entrada', 'solicitud', 'El usuario solicita anular su compra dentro de la ventana de política permitida', 'Usuario/asistente'),
  ('creacion_publicacion_evento', 'Creación y publicación de evento', 'solicitud', 'El organizador solicita alta de un nuevo evento en la plataforma, con fechas, aforo y precios', 'Organizador (cliente)'),
  ('cambio_asiento_categoria_entrada', 'Cambio de asiento o categoría de entrada', 'solicitud', 'El usuario pide reasignar su ticket a otro asiento disponible dentro del mismo evento', 'Usuario/asistente'),
  ('pago_no_procesado_cobro_duplicado', 'Pago no procesado o cobro duplicado', 'incidente', 'La pasarela de pago falla, rechaza indebidamente o cobra dos veces por una misma compra', 'Usuario/asistente'),
  ('qr_rechazado_en_puerta', 'QR rechazado en puerta', 'incidente', 'El código QR válido no es reconocido por el sistema de validación al momento del ingreso', 'Usuario/asistente o personal de validación'),
  ('correo_confirmacion_no_entregado', 'Correo de confirmación no entregado', 'incidente', 'El pago se procesó correctamente pero el ticket digital nunca llegó al correo del usuario', 'Usuario/asistente'),
  ('panel_ventas_desincronizado', 'Panel de ventas desincronizado', 'incidente', 'El organizador ve cifras de ventas o disponibilidad que no corresponden al estado real de la base de datos', 'Organizador (cliente)');

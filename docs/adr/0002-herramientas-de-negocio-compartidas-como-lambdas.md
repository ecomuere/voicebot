# ADR 0002 — Herramientas de negocio compartidas como Lambdas

- **Estado**: Aceptada
- **Fecha**: 2026-06-12
- **Decisores**: Iván Llorente

## Contexto

Tras el [ADR 0001](0001-telefonia-con-amazon-connect-nativo.md), el sistema
tiene dos "cerebros conversacionales": el AI agent nativo de Amazon Connect
(teléfono) y el agente Strands de este repo (web). Ambos necesitan ejecutar las
mismas capacidades de negocio (consultar pedidos, reservar, escribir en el
CRM...). Implementarlas dos veces garantiza divergencia: el bot del teléfono y
el del navegador acabarían respondiendo distinto a la misma pregunta.

## Decisión

Cada capacidad de negocio se implementa **una sola vez como una función Lambda**
(`lambdas/<capacidad>/`), invocada por ambos canales:

- **Connect**: la Lambda se asocia a la instancia
  (`aws_connect_lambda_function_association`) y el AI agent la invoca como
  acción del contact flow.
- **Strands**: una tool fina en `adapters/tools.py` invoca la Lambda vía boto3
  (`lambda:InvokeFunction`) y formatea la respuesta para voz.

Contrato del handler (impuesto por Connect, adoptado para ambos llamantes):

- **Entrada**: el handler normaliza ambos formatos — el evento de Connect
  (`{"Details": {"Parameters": {...}}}`) y la invocación directa (JSON plano).
- **Salida**: mapa plano `str -> str` (requisito de Connect para los atributos
  de contacto).

Primera implementación de referencia: `lambdas/order_status` (estado de
pedidos), desplegada por el stack `infra/terraform/tools` y consumida por la
tool `get_order_status`.

## Consecuencias

### Positivas

- Una única fuente de verdad por capacidad: los dos canales responden igual.
- Las Lambdas son puro Python testeable sin AWS (los tests cubren ambos
  formatos de evento y el contrato de salida).
- Añadir una capacidad nueva es un patrón repetible: carpeta en `lambdas/`,
  recurso en el stack `tools`, tool fina en `adapters/tools.py` y, en Connect,
  una acción del AI agent.

### Negativas

- Un salto de red extra por consulta desde el agente Strands (latencia de
  invocación de Lambda, normalmente decenas de ms — aceptable en una
  conversación de voz).
- El contrato "mapa plano de strings" es menos expresivo que JSON anidado;
  capacidades complejas tendrán que aplanar su respuesta.

### Neutras

- Los roles de EC2 y AgentCore obtienen `lambda:InvokeFunction` limitado al
  patrón `voicebot-*`; la tool se desactiva limpiamente si
  `VOICEBOT_ORDER_STATUS_FUNCTION` no está definida (entorno local).

## Referencias

- Implementación: [`lambdas/order_status`](../../lambdas/order_status),
  [`infra/terraform/tools`](../../infra/terraform/tools),
  `src/voicebot/adapters/tools.py`
- [Invoke AWS Lambda functions — Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html)

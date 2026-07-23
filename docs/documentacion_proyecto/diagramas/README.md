# Diagramas del proyecto

Esta carpeta separa las fuentes editables de los formatos destinados a lectura y presentación.

| Carpeta | Formato | Uso |
|---|---|---|
| `fuente_mermaid/` | `.mmd` | Fuente textual canónica, revisable junto con el código. |
| `editables/` | `.drawio` | Editable gráfico principal para ajustes visuales en diagrams.net. |
| `exportados/` | `.svg` y, cuando se produzcan, `.png` | Formato de lectura e inserción en Word y PowerPoint. |

## Cómo actualizar un diagrama

1. Verificar el comportamiento contra el código actual.
2. Actualizar primero el `.mmd` homónimo en `fuente_mermaid/`.
3. Replicar manualmente el cambio en el `.drawio` de `editables/`.
4. Exportar desde diagrams.net un nuevo SVG a `exportados/`; generar PNG solo si la herramienta de destino lo requiere.
5. Comprobar títulos, conexiones, legibilidad y enlaces relativos en Markdown.

Los seis diagramas fueron sincronizados después de la revisión técnica. Los archivos `.mmd` constituyen la fuente textual canónica, los `.drawio` son los editables visuales y los `.svg` corresponden a las versiones publicadas.

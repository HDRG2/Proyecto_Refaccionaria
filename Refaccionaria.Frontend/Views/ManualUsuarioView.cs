using Microsoft.UI;
using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

using System;
using System.Collections.Generic;
using System.Linq;

using Windows.UI;

namespace Refaccionaria.Frontend.Views;

// =============================================================
// MANUAL DE USUARIO DENTRO DEL PROGRAMA
//
// Control construido solo con código (sin XAML) para poder
// mostrarlo en el Panel de Administrador y en una ventana
// desde la pantalla de Mostrador.
//
// mostrarAdministrador = true  -> muestra todas las secciones
// mostrarAdministrador = false -> solo las secciones de Mostrador
// =============================================================

public sealed class ManualUsuarioView : UserControl
{
    // =========================================================
    // COLORES (mismos tonos del sistema)
    // =========================================================

    private static readonly Color Amarillo = ColorHelper.FromArgb(255, 255, 193, 7);
    private static readonly Color GrisOscuro = ColorHelper.FromArgb(255, 45, 45, 45);
    private static readonly Color GrisTexto = ColorHelper.FromArgb(255, 85, 85, 85);
    private static readonly Color GrisFondo = ColorHelper.FromArgb(255, 244, 244, 244);
    private static readonly Color Borde = ColorHelper.FromArgb(255, 224, 224, 224);
    private static readonly Color FondoNota = ColorHelper.FromArgb(255, 255, 248, 225);


    // =========================================================
    // MODELO DEL CONTENIDO
    // =========================================================

    private enum TipoBloque { Parrafo, Pasos, Lista, Nota, Tabla }

    private sealed record Bloque(TipoBloque Tipo, string[] Lineas);

    private sealed record Seccion(
        string Icono,
        string Titulo,
        bool SoloAdministrador,
        Bloque[] Bloques);

    private static Bloque P(string texto) => new(TipoBloque.Parrafo, new[] { texto });
    private static Bloque Pasos(params string[] pasos) => new(TipoBloque.Pasos, pasos);
    private static Bloque Lista(params string[] puntos) => new(TipoBloque.Lista, puntos);
    private static Bloque Nota(string texto) => new(TipoBloque.Nota, new[] { texto });

    // Cada fila: "Columna 1|Columna 2|Columna 3". La primera fila es el encabezado.
    private static Bloque Tabla(params string[] filas) => new(TipoBloque.Tabla, filas);


    private readonly Dictionary<string, FrameworkElement> _tarjetas = new();

    private readonly ScrollViewer _scroll = new();


    // =========================================================
    // CONSTRUCTOR
    // =========================================================

    public ManualUsuarioView(bool mostrarAdministrador)
    {
        RequestedTheme = ElementTheme.Light;

        List<Seccion> secciones =
            ObtenerSecciones()
            .Where(s => mostrarAdministrador || !s.SoloAdministrador)
            .ToList();

        Content = ConstruirInterfaz(secciones, mostrarAdministrador);
    }


    // =========================================================
    // INTERFAZ
    // =========================================================

    private UIElement ConstruirInterfaz(
        List<Seccion> secciones,
        bool mostrarAdministrador)
    {
        Grid raiz = new()
        {
            Background = new SolidColorBrush(GrisFondo)
        };

        raiz.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        raiz.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });


        // ---------------- ENCABEZADO ----------------

        StackPanel encabezado = new()
        {
            Margin = new Thickness(0, 0, 0, 16)
        };

        encabezado.Children.Add(new TextBlock
        {
            Text = "Manual de usuario",
            FontSize = 26,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(GrisOscuro)
        });

        encabezado.Children.Add(new TextBlock
        {
            Text = mostrarAdministrador
                ? "Guía completa del sistema de la Refaccionaria El Pistón: mostrador y administración."
                : "Guía para vender en mostrador con el sistema de la Refaccionaria El Pistón.",
            FontSize = 14,
            TextWrapping = TextWrapping.Wrap,
            Foreground = new SolidColorBrush(GrisTexto),
            Margin = new Thickness(0, 4, 0, 0)
        });

        raiz.Children.Add(encabezado);


        // ---------------- CUERPO: ÍNDICE + CONTENIDO ----------------

        Grid cuerpo = new()
        {
            ColumnSpacing = 20
        };

        cuerpo.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(230) });
        cuerpo.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

        Grid.SetRow(cuerpo, 1);
        raiz.Children.Add(cuerpo);


        // Índice

        ListView indice = new()
        {
            SelectionMode = ListViewSelectionMode.Single,
            Background = new SolidColorBrush(Colors.White),
            BorderBrush = new SolidColorBrush(Borde),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(0, 6, 0, 6),
            ItemsSource = secciones.Select(s => $"{s.Icono}  {s.Titulo}").ToList()
        };

        indice.SelectionChanged += (_, _) =>
        {
            if (indice.SelectedIndex < 0 ||
                indice.SelectedIndex >= secciones.Count)
            {
                return;
            }

            string titulo = secciones[indice.SelectedIndex].Titulo;

            if (_tarjetas.TryGetValue(titulo, out FrameworkElement? tarjeta))
            {
                tarjeta.StartBringIntoView(new BringIntoViewOptions
                {
                    VerticalAlignmentRatio = 0,
                    AnimationDesired = true
                });
            }
        };

        cuerpo.Children.Add(indice);


        // Contenido

        StackPanel contenido = new()
        {
            Spacing = 14,
            Padding = new Thickness(0, 0, 14, 20)
        };

        foreach (Seccion seccion in secciones)
        {
            FrameworkElement tarjeta = CrearTarjeta(seccion);
            _tarjetas[seccion.Titulo] = tarjeta;
            contenido.Children.Add(tarjeta);
        }

        _scroll.Content = contenido;
        _scroll.VerticalScrollBarVisibility = ScrollBarVisibility.Auto;

        Grid.SetColumn(_scroll, 1);
        cuerpo.Children.Add(_scroll);

        return raiz;
    }


    // =========================================================
    // TARJETA DE UNA SECCIÓN
    // =========================================================

    private FrameworkElement CrearTarjeta(Seccion seccion)
    {
        StackPanel panel = new()
        {
            Spacing = 10
        };

        StackPanel titulo = new()
        {
            Orientation = Orientation.Horizontal,
            Spacing = 10
        };

        titulo.Children.Add(new TextBlock
        {
            Text = seccion.Icono,
            FontSize = 20,
            VerticalAlignment = VerticalAlignment.Center
        });

        titulo.Children.Add(new TextBlock
        {
            Text = seccion.Titulo,
            FontSize = 19,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(GrisOscuro),
            VerticalAlignment = VerticalAlignment.Center
        });

        if (seccion.SoloAdministrador)
        {
            titulo.Children.Add(new Border
            {
                Background = new SolidColorBrush(Amarillo),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(8, 2, 8, 2),
                VerticalAlignment = VerticalAlignment.Center,
                Child = new TextBlock
                {
                    Text = "ADMINISTRADOR",
                    FontSize = 10,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush(GrisOscuro)
                }
            });
        }

        panel.Children.Add(titulo);

        panel.Children.Add(new Border
        {
            Height = 3,
            Width = 48,
            HorizontalAlignment = HorizontalAlignment.Left,
            Background = new SolidColorBrush(Amarillo),
            CornerRadius = new CornerRadius(2),
            Margin = new Thickness(0, 0, 0, 4)
        });

        foreach (Bloque bloque in seccion.Bloques)
        {
            panel.Children.Add(CrearBloque(bloque));
        }

        return new Border
        {
            Background = new SolidColorBrush(Colors.White),
            BorderBrush = new SolidColorBrush(Borde),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(8),
            Padding = new Thickness(24, 20, 24, 22),
            Child = panel
        };
    }


    // =========================================================
    // BLOQUES DE TEXTO
    // =========================================================

    private static UIElement CrearBloque(Bloque bloque)
    {
        switch (bloque.Tipo)
        {
            case TipoBloque.Pasos:
                return CrearLista(bloque.Lineas, numerada: true);

            case TipoBloque.Lista:
                return CrearLista(bloque.Lineas, numerada: false);

            case TipoBloque.Nota:
                return new Border
                {
                    Background = new SolidColorBrush(FondoNota),
                    BorderBrush = new SolidColorBrush(Amarillo),
                    BorderThickness = new Thickness(4, 0, 0, 0),
                    CornerRadius = new CornerRadius(4),
                    Padding = new Thickness(14, 10, 14, 10),
                    Child = Texto(bloque.Lineas[0])
                };

            case TipoBloque.Tabla:
                return CrearTabla(bloque.Lineas);

            default:
                return Texto(bloque.Lineas[0]);
        }
    }


    private static TextBlock Texto(
        string texto,
        bool negritas = false)
    {
        return new TextBlock
        {
            Text = texto,
            FontSize = 14,
            LineHeight = 21,
            TextWrapping = TextWrapping.Wrap,
            FontWeight = negritas ? FontWeights.SemiBold : FontWeights.Normal,
            Foreground = new SolidColorBrush(GrisOscuro)
        };
    }


    private static UIElement CrearLista(
        string[] lineas,
        bool numerada)
    {
        StackPanel lista = new()
        {
            Spacing = 6,
            Margin = new Thickness(4, 0, 0, 0)
        };

        for (int i = 0; i < lineas.Length; i++)
        {
            Grid fila = new()
            {
                ColumnSpacing = 8
            };

            fila.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(26) });
            fila.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            UIElement marca = numerada
                ? new Border
                {
                    Width = 22,
                    Height = 22,
                    CornerRadius = new CornerRadius(11),
                    Background = new SolidColorBrush(GrisOscuro),
                    VerticalAlignment = VerticalAlignment.Top,
                    Child = new TextBlock
                    {
                        Text = (i + 1).ToString(),
                        FontSize = 12,
                        FontWeight = FontWeights.Bold,
                        Foreground = new SolidColorBrush(Amarillo),
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    }
                }
                : new TextBlock
                {
                    Text = "•",
                    FontSize = 16,
                    Foreground = new SolidColorBrush(GrisTexto),
                    HorizontalAlignment = HorizontalAlignment.Center
                };

            fila.Children.Add(marca);

            TextBlock texto = Texto(lineas[i]);
            Grid.SetColumn(texto, 1);
            fila.Children.Add(texto);

            lista.Children.Add(fila);
        }

        return lista;
    }


    private static UIElement CrearTabla(string[] filas)
    {
        Grid tabla = new()
        {
            BorderBrush = new SolidColorBrush(Borde),
            BorderThickness = new Thickness(1),
            CornerRadius = new CornerRadius(6)
        };

        int columnas = filas[0].Split('|').Length;

        for (int c = 0; c < columnas; c++)
        {
            tabla.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        }

        for (int f = 0; f < filas.Length; f++)
        {
            tabla.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            string[] celdas = filas[f].Split('|');
            bool encabezado = f == 0;

            for (int c = 0; c < columnas; c++)
            {
                Border celda = new()
                {
                    Padding = new Thickness(10, 8, 10, 8),
                    Background = new SolidColorBrush(
                        encabezado ? GrisOscuro : (f % 2 == 0 ? GrisFondo : Colors.White)),
                    Child = new TextBlock
                    {
                        Text = c < celdas.Length ? celdas[c] : string.Empty,
                        FontSize = 13,
                        TextWrapping = TextWrapping.Wrap,
                        FontWeight = encabezado ? FontWeights.SemiBold : FontWeights.Normal,
                        Foreground = new SolidColorBrush(encabezado ? Colors.White : GrisOscuro)
                    }
                };

                Grid.SetRow(celda, f);
                Grid.SetColumn(celda, c);
                tabla.Children.Add(celda);
            }
        }

        return tabla;
    }


    // =========================================================
    // CONTENIDO DEL MANUAL
    // =========================================================

    private static IEnumerable<Seccion> ObtenerSecciones()
    {
        // ---------------- GENERAL ----------------

        yield return new Seccion("👋", "Introducción", false, new[]
        {
            P("Este sistema controla el inventario y las ventas de la Refaccionaria El Pistón. Tiene dos modos de trabajo:"),
            Tabla(
                "Modo|Para quién|Qué puede hacer",
                "Mostrador|Vendedores|Buscar piezas, armar el carrito, cobrar, ver el ticket y usar el asistente virtual.",
                "Administrador|Dueño o encargado|Inventario, productos, autos, marcas, categorías, empleados y reportes de ventas.")
        });

        yield return new Seccion("🔑", "Iniciar sesión", false, new[]
        {
            Pasos(
                "Abre el programa Refaccionaria El Pistón.",
                "Elige tu modo arriba del formulario: «Mostrador» o «Administrador».",
                "Escribe tu Usuario y tu Contraseña. Con el botón «Mostrar» puedes ver la contraseña que escribiste.",
                "Presiona «Entrar al sistema» o la tecla Enter."),
            Nota("Si tu cuenta es de administrador debes elegir «Administrador»; si eres vendedor, «Mostrador». Si tu usuario está desactivado, pide al administrador que lo reactive.")
        });


        // ---------------- MOSTRADOR ----------------

        yield return new Seccion("🔍", "Buscar una refacción", false, new[]
        {
            Lista(
                "Escribe en la barra «Busca por pieza, código, marca, modelo o año…». Los resultados se filtran mientras escribes.",
                "Usa las categorías del lado izquierdo (Frenos, Filtros, Suspensión, etc.) para ver solo un tipo de pieza.",
                "Para encontrar lo que le queda al auto del cliente, elige la Marca, el Modelo y el Año del auto.",
                "Ordena por nombre, por precio (menor a mayor o mayor a menor) o con «Más existencia primero».",
                "«Quitar filtros» regresa a la lista completa."),
            P("Cada producto muestra su precio, su existencia y los autos con los que es compatible.")
        });

        yield return new Seccion("🛒", "Armar el carrito", false, new[]
        {
            Pasos(
                "Presiona «Agregar» en la pieza que quiere el cliente.",
                "En el carrito usa «+» y «-» para cambiar la cantidad, o «✕» para quitar una pieza.",
                "«Vaciar carrito» borra todo para empezar de nuevo."),
            P("El carrito muestra el Subtotal, el IVA (16 %) y el Total."),
            Nota("No puedes vender más piezas de las que hay en existencia.")
        });

        yield return new Seccion("💵", "Cobrar una venta", false, new[]
        {
            Pasos(
                "Presiona «COBRAR».",
                "En «¿Cómo va a pagar?» elige «Efectivo» o «Tarjeta».",
                "Efectivo: escribe la cantidad en «¿Con cuánto paga?». El sistema calcula el cambio; si el dinero no alcanza muestra «Faltan $…».",
                "Tarjeta: aparece un código QR. El cliente lo escanea con su teléfono y el sistema muestra «Esperando pago…» y «Procesando pago…» hasta aprobarlo.",
                "Presiona «Confirmar venta». Si el cliente se arrepiente, presiona «Cancelar»."),
            Nota("En esta versión el pago con tarjeta es una simulación: no se realiza ningún cargo real.")
        });

        yield return new Seccion("🧾", "Ticket de venta", false, new[]
        {
            P("Al confirmar aparece «Venta registrada» con el ticket: folio, productos, subtotal, IVA, total y forma de pago."),
            P("Presiona «Iniciar otra venta» para atender al siguiente cliente. La existencia de las piezas vendidas se descuenta automáticamente.")
        });

        yield return new Seccion("🔧", "Asistente virtual", false, new[]
        {
            P("Presiona el botón del asistente para abrir el chat, escribe tu pregunta en «Escribe tu pregunta…» y presiona «Enviar». Ejemplos:"),
            Lista(
                "¿Tienes balatas para Tsuru 2010?",
                "¿Cuánto cuestan 3 filtros de aceite?",
                "¿Para qué sirve un amortiguador?"),
            Nota("El asistente solo consulta información: no puede cambiar precios ni existencias. Con «Nueva conversación» empiezas de cero.")
        });

        yield return new Seccion("↪", "Cerrar sesión", false, new[]
        {
            P("En Mostrador presiona el botón «↪» (Cerrar sesión) de la parte superior. En el Panel de Administrador presiona «Salir». Regresarás a la pantalla de inicio.")
        });


        // ---------------- ADMINISTRADOR ----------------

        yield return new Seccion("📦", "Inventario", true, new[]
        {
            P("Muestra el resumen del almacén: total de productos, unidades en almacén, valor del inventario y productos con stock bajo (5 piezas o menos)."),
            P("Puedes buscar por nombre, código, marca o categoría, aplicar filtros y ordenar la lista.")
        });

        yield return new Seccion("➕", "Agregar un producto", true, new[]
        {
            Pasos(
                "Presiona «+ NUEVO PRODUCTO».",
                "Llena los campos obligatorios (*): Código, Nombre de la pieza, Marca, Categoría, Precio y Existencia.",
                "En «Autos compatibles» marca los autos a los que les queda la pieza, o activa «Sirve para cualquier auto» si es universal.",
                "Presiona «GUARDAR»."),
            Nota("El código acepta letras, números y guion. El precio acepta solo números con máximo 2 decimales (por ejemplo 85.50).")
        });

        yield return new Seccion("✎", "Editar un producto", true, new[]
        {
            Pasos(
                "Entra a «Editar producto» y busca la pieza.",
                "Selecciónala y presiona «Editar».",
                "Corrige los datos y presiona «GUARDAR»."),
            P("Desde el formulario también puedes presionar «RETIRAR PRODUCTO» para quitarlo del inventario sin borrarlo.")
        });

        yield return new Seccion("🗑", "Productos retirados", true, new[]
        {
            P("Aquí están los productos que retiraste; no aparecen en el mostrador."),
            Lista(
                "«REACTIVAR / REABASTECER»: le agregas existencia y vuelve a estar a la venta.",
                "«ELIMINAR DEFINITIVAMENTE»: lo borra para siempre (pide confirmación).")
        });

        yield return new Seccion("🚗", "Autos, marcas y categorías", true, new[]
        {
            P("En «Agregar elementos» hay tres secciones: Autos, Marcas de piezas y Categorías."),
            Lista(
                "Agregar: llena los datos (para un auto: marca, modelo, año inicio y año fin) y presiona «+ AGREGAR».",
                "Editar: elige un elemento de la lista, corrige los datos y presiona «✎ EDITAR». Los productos y ventas que ya lo usan muestran el nombre corregido.")
        });

        yield return new Seccion("👥", "Empleados", true, new[]
        {
            Pasos(
                "Presiona «+ NUEVO EMPLEADO».",
                "Llena Nombre completo, Usuario, Contraseña, teléfono y rol.",
                "Presiona «GUARDAR»."),
            P("Para modificar a un empleado selecciónalo y presiona «Editar» (o da doble clic). El interruptor «Empleado activo» permite desactivarlo sin borrarlo: no podrá iniciar sesión hasta que lo reactives.")
        });

        yield return new Seccion("▥", "Reportes de ventas", true, new[]
        {
            Pasos(
                "Elige el periodo: Hoy, Ayer, Últimos 7 días, Últimas 2 semanas, Últimas 3 semanas, Este mes, Todo el historial o Personalizado (fechas Desde y Hasta).",
                "Revisa los indicadores: Total vendido, Ventas registradas, Piezas vendidas y Producto más vendido.",
                "En la tabla presiona «Ver Ticket» para ver el detalle de una venta.",
                "Presiona «↓ DESCARGAR REPORTE» para guardar el PDF en la carpeta Reportes.")
        });

        yield return new Seccion("💾", "Respaldos", true, new[]
        {
            P("El sistema guarda una copia automática de cada archivo antes de cualquier cambio (conserva las últimas 10) en la carpeta Refaccionaria.Backend\\Backups. Si una venta falla a medias, todo regresa a como estaba."),
            Nota("Se recomienda copiar la carpeta Refaccionaria.Backend\\Data a una USB o a la nube al menos una vez por semana.")
        });


        // ---------------- AYUDA ----------------

        yield return new Seccion("⚠", "Mensajes frecuentes", false, new[]
        {
            Tabla(
                "Mensaje|Qué significa|Qué hacer",
                "El usuario o la contraseña son incorrectos.|Datos mal escritos.|Revisa mayúsculas y vuelve a intentar.",
                "Esta cuenta es de administrador.|Elegiste Mostrador con una cuenta de administrador.|Presiona el botón «Administrador».",
                "Este usuario no tiene permisos de administrador.|Un vendedor eligió Administrador.|Elige «Mostrador».",
                "Este usuario está desactivado.|La cuenta fue desactivada.|Pide al administrador que la reactive.",
                "No hay suficiente existencia de …|Quieres vender más piezas de las que hay.|Baja la cantidad o pide que se reabastezca.",
                "Faltan $…|El efectivo no alcanza.|Pide la cantidad completa.",
                "Los campos marcados con * son obligatorios.|Falta un dato.|Completa los campos con *.",
                "El asistente no responde.|El servidor de IA u Ollama no están activos.|Cierra y abre el programa; verifica que Ollama esté abierto.")
        });

        yield return new Seccion("❓", "Preguntas frecuentes", false, new[]
        {
            P("¿Puedo vender una pieza que no aparece? No. El administrador debe darla de alta o reactivarla en Productos retirados."),
            P("¿Qué diferencia hay entre retirar y eliminar un producto? Retirar lo oculta y se puede recuperar; eliminar definitivamente lo borra para siempre."),
            P("¿Cómo sé qué debo resurtir? En Inventario, los productos con 5 piezas o menos aparecen como stock bajo.")
        });
    }
}

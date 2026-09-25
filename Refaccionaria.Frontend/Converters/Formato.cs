using System;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Linq;
using Microsoft.UI;
using Microsoft.UI.Xaml.Media;

namespace Refaccionaria.Frontend.Converters;

/// <summary>
/// Funciones de formato para usar con x:Bind en PanelAdmin.xaml.
/// WinUI 3 no soporta StringFormat en los bindings ni DataTrigger,
/// así que el texto y el color salen de estas funciones.
/// </summary>
public static class Formato
{
    private static readonly CultureInfo Mexico = new("es-MX");

    private static readonly SolidColorBrush Verde = new(ColorHelper.FromArgb(255, 0x2E, 0x7D, 0x32));
    private static readonly SolidColorBrush Rojo = new(ColorHelper.FromArgb(255, 0xC6, 0x28, 0x28));

    public static string Moneda(decimal valor) => valor.ToString("C", Mexico);

    public static string Fecha(DateTime fecha) => fecha.ToString("dd/MM/yyyy HH:mm");

    public static string Existencia(int stock) => $"{stock} en existencia";

    public static string EstadoStock(int stock, bool stockBajo) =>
        stock == 0 ? "Agotado" : stockBajo ? "Por resurtir" : "Disponible";

    public static Brush ColorStock(bool stockBajo) => stockBajo ? Rojo : Verde;

    public static string EstadoActivo(bool activo) => activo ? "Activo" : "Inactivo";

    public static string Compatibilidad(bool esUniversal, ObservableCollection<string> autos)
    {
        if (esUniversal) return "Universal (todos los autos)";
        if (autos == null || autos.Count == 0) return "Sin autos asignados";
        return string.Join(", ", autos);
    }
}

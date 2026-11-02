using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

using System;
using System.IO;

namespace Refaccionaria.Frontend.Views;

// =============================================================
// MANUAL DE USUARIO (MOSTRADOR)
//
// El botón "?" de la parte superior abre el manual en una
// ventana aparte, con las secciones que usa el vendedor.
// Si la ventana ya está abierta, solo se trae al frente.
// =============================================================

public sealed partial class VentaPage : Page
{
    private static Window? _ventanaManual;


    private void AbrirManual_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (_ventanaManual != null)
        {
            _ventanaManual.Activate();
            return;
        }

        Window ventana = new()
        {
            Title = "Manual de usuario - Refaccionaria El Pistón"
        };

        ventana.Content = new Grid
        {
            Padding = new Thickness(28, 24, 28, 0),
            Background = new Microsoft.UI.Xaml.Media.SolidColorBrush(
                Microsoft.UI.ColorHelper.FromArgb(255, 244, 244, 244)),
            Children =
            {
                new ManualUsuarioView(mostrarAdministrador: false)
            }
        };

        try
        {
            ventana.AppWindow.Resize(
                new Windows.Graphics.SizeInt32(1000, 760));

            string icono = Path.Combine(
                AppContext.BaseDirectory,
                "Assets",
                "LogoPiston.ico");

            if (File.Exists(icono))
            {
                ventana.AppWindow.SetIcon(icono);
            }
        }
        catch
        {
            // Si no se puede cambiar el tamaño o el icono,
            // la ventana se abre con los valores por defecto.
        }

        ventana.Closed += (_, _) => _ventanaManual = null;

        _ventanaManual = ventana;
        ventana.Activate();
    }
}

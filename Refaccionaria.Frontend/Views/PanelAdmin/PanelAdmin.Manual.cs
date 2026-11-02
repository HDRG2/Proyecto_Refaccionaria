using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace Refaccionaria.Frontend.Views;

// =============================================================
// MANUAL DE USUARIO (PANEL DE ADMINISTRADOR)
//
// Muestra el manual completo dentro del área principal cuando
// se elige "Manual de usuario" en el menú de la izquierda.
// =============================================================

public sealed partial class PanelAdmin : Page
{
    private ManualUsuarioView? _manualUsuario;


    private void MostrarManual()
    {
        VistaInventario.Visibility = Visibility.Collapsed;
        VistaEditarProducto.Visibility = Visibility.Collapsed;
        VistaProductosRetirados.Visibility = Visibility.Collapsed;
        VistaEmpleados.Visibility = Visibility.Collapsed;
        VistaReportes.Visibility = Visibility.Collapsed;
        VistaAgregarElementos.Visibility = Visibility.Collapsed;
        Formulario.Visibility = Visibility.Collapsed;

        // Se crea una sola vez, la primera vez que se abre
        if (_manualUsuario == null)
        {
            _manualUsuario = new ManualUsuarioView(mostrarAdministrador: true);
            VistaManual.Children.Add(_manualUsuario);
        }

        VistaManual.Visibility = Visibility.Visible;
    }
}

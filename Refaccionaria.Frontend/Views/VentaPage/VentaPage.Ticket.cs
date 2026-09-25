using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Views
{
    public sealed partial class VentaPage : Page
    {
        // =========================================================
        // TICKET
        // =========================================================

        public void AlternarTicket()
        {
            if (_panelAbierto)
            {
                CerrarTicket();
            }
            else
            {
                AbrirTicket();
            }
        }


        public void AbrirTicket()
        {
            if (_panelAbierto)
            {
                return;
            }


            _panelAbierto = true;

            AnimarPanel(
                ANCHO_PANEL
            );
        }


        public void CerrarTicket()
        {
            if (!_panelAbierto)
            {
                return;
            }


            _panelAbierto = false;

            AnimarPanel(
                0
            );
        }


        private void AnimarPanel(
            double anchoFinal)
        {
            DoubleAnimation animacion =
                new()
                {
                    To = anchoFinal,

                    Duration =
                        new Duration(
                            TimeSpan.FromMilliseconds(
                                180
                            )
                        ),

                    EnableDependentAnimation =
                        true
                };


            Storyboard.SetTarget(
                animacion,
                PanelTicket
            );


            Storyboard.SetTargetProperty(
                animacion,
                "Width"
            );


            Storyboard storyboard =
                new();


            storyboard.Children.Add(
                animacion
            );


            storyboard.Begin();
        }


        private void CerrarTicket_Click(
            object sender,
            RoutedEventArgs e)
        {
            CerrarTicket();
        }


        private void VerTicket_Click(
            object sender,
            RoutedEventArgs e)
        {
            AlternarTicket();
        }


        // =========================================================
        // AGREGAR PRODUCTO
        // =========================================================

        private async void Agregar_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (sender is not Button boton)
            {
                return;
            }


            if (boton.DataContext is not Refaccion refaccion)
            {
                return;
            }


            if (!refaccion.Activo)
            {
                await MostrarMensaje(
                    "Producto no disponible",
                    "Este producto está retirado."
                );

                return;
            }


            if (refaccion.Stock <= 0)
            {
                await MostrarMensaje(
                    "Producto agotado",
                    $"No hay existencia de \"{refaccion.Nombre}\"."
                );

                return;
            }


            DetalleVenta? linea =
                _ticket.FirstOrDefault(
                    d =>
                        d.RefaccionId ==
                        refaccion.Id
                );


            if (linea == null)
            {
                linea =
                    new DetalleVenta
                    {
                        RefaccionId =
                            refaccion.Id,

                        Cantidad =
                            1,

                        PrecioUnitario =
                            refaccion.Precio,

                        Refaccion =
                            refaccion
                    };


                _ticket.Add(
                    linea
                );
            }
            else
            {
                if (linea.Cantidad >=
                    refaccion.Stock)
                {
                    await MostrarMensaje(
                        "Existencia insuficiente",
                        $"Solo hay {refaccion.Stock} unidades disponibles de \"{refaccion.Nombre}\"."
                    );

                    return;
                }


                linea.Cantidad++;
            }


            ActualizarTotales();
        }


        // =========================================================
        // AUMENTAR CANTIDAD
        // =========================================================

        private async void Mas_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (sender is not Button boton)
            {
                return;
            }


            if (boton.DataContext is not DetalleVenta linea)
            {
                return;
            }


            Refaccion? refaccion =
                linea.Refaccion;


            if (refaccion == null)
            {
                refaccion =
                    _refacciones.FirstOrDefault(
                        r =>
                            r.Id ==
                            linea.RefaccionId
                    );
            }


            if (refaccion == null)
            {
                return;
            }


            if (linea.Cantidad >=
                refaccion.Stock)
            {
                await MostrarMensaje(
                    "Existencia insuficiente",
                    $"Solo hay {refaccion.Stock} unidades disponibles de \"{refaccion.Nombre}\"."
                );

                return;
            }


            linea.Cantidad++;

            ActualizarTotales();
        }


        // =========================================================
        // DISMINUIR CANTIDAD
        // =========================================================

        private void Menos_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (sender is not Button boton)
            {
                return;
            }


            if (boton.DataContext is not DetalleVenta linea)
            {
                return;
            }


            if (linea.Cantidad > 1)
            {
                linea.Cantidad--;
            }
            else
            {
                _ticket.Remove(
                    linea
                );
            }


            ActualizarTotales();
        }


        // =========================================================
        // QUITAR PRODUCTO
        // =========================================================

        private void Quitar_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (sender is not Button boton)
            {
                return;
            }


            if (boton.DataContext is not DetalleVenta linea)
            {
                return;
            }


            _ticket.Remove(
                linea
            );


            ActualizarTotales();
        }


        // =========================================================
        // VACIAR TICKET
        // =========================================================

        private async void Vaciar_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (_ticket.Count == 0)
            {
                return;
            }


            ContentDialog dialogo =
                new()
                {
                    Title =
                        "Vaciar carrito",

                    Content =
                        "¿Deseas quitar todos los productos del carrito?",

                    PrimaryButtonText =
                        "Vaciar",

                    CloseButtonText =
                        "Cancelar",

                    DefaultButton =
                        ContentDialogButton.Close,

                    XamlRoot =
                        XamlRoot
                };


            ContentDialogResult resultado =
                await dialogo.ShowAsync();


            if (resultado !=
                ContentDialogResult.Primary)
            {
                return;
            }


            _ticket.Clear();

            ActualizarTotales();
        }


        // =========================================================
        // ACTUALIZAR TOTALES
        // =========================================================

        private void ActualizarTotales()
        {
            int piezas =
                _ticket.Sum(
                    l => l.Cantidad
                );


            _subtotal =
                _ticket.Sum(
                    l => l.Subtotal
                );


            /*
             * En este diseño estamos tomando el precio de las
             * refacciones como precio antes de IVA.
             */

            _iva =
                Math.Round(
                    _subtotal * 0.16m,
                    2
                );


            _total =
                _subtotal + _iva;


            // -----------------------------------------------------
            // PANEL DEL TICKET
            // -----------------------------------------------------

            TxtPiezas.Text =
                piezas == 1
                    ? "1 pieza"
                    : $"{piezas} piezas";


            TxtSubtotal.Text =
                _subtotal.ToString("C");


            TxtIva.Text =
                _iva.ToString("C");


            TxtTotal.Text =
                _total.ToString("C");


            // -----------------------------------------------------
            // CÍRCULO ROJO DEL CARRITO
            // -----------------------------------------------------

            TxtBotonTicket.Text =
                piezas.ToString();


            // -----------------------------------------------------
            // ESTADO VACÍO
            // -----------------------------------------------------

            TxtTicketVacio.Visibility =
                _ticket.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;


            BtnCobrar.IsEnabled =
                _ticket.Count > 0;


            BtnVaciar.IsEnabled =
                _ticket.Count > 0;


            TicketActualizado?.Invoke(
                piezas
            );
        }
    }
}
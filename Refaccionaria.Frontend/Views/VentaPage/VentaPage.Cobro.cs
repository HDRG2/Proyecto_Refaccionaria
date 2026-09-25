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
        // ABRIR COBRO
        // =========================================================

        private void Cobrar_Click(
            object sender,
            RoutedEventArgs e)
        {
            if (_ticket.Count == 0)
            {
                return;
            }


            CapaCobro.Visibility =
                Visibility.Visible;


            PanelCobro.Visibility =
                Visibility.Visible;


            PanelExito.Visibility =
                Visibility.Collapsed;


            int piezas =
                _ticket.Sum(
                    l => l.Cantidad
                );


            TxtPiezasCobro.Text =
                piezas == 1
                    ? "1 pieza"
                    : $"{piezas} piezas";


            TxtTotalCobro.Text =
                _total.ToString("C");


            RbEfectivo.IsChecked =
                true;


            _metodoPago =
                "Efectivo";


            PanelEfectivo.Visibility =
                Visibility.Visible;


            PanelTarjeta.Visibility =
                Visibility.Collapsed;


            TxtRecibido.Text =
                string.Empty;


            TxtCambio.Text =
                "Cambio: $0.00";


            BtnConfirmar.IsEnabled =
                false;


            TxtRecibido.Focus(
                FocusState.Programmatic
            );
        }


        // =========================================================
        // MÉTODO DE PAGO
        // =========================================================

        private void MetodoPago_Checked(
            object sender,
            RoutedEventArgs e)
        {
            /*
             * Durante InitializeComponent algunos controles
             * todavía pueden no estar disponibles.
             */

            if (PanelEfectivo == null ||
                PanelTarjeta == null ||
                BtnConfirmar == null)
            {
                return;
            }


            if (RbTarjeta.IsChecked == true)
            {
                _metodoPago =
                    "Tarjeta";


                PanelEfectivo.Visibility =
                    Visibility.Collapsed;


                PanelTarjeta.Visibility =
                    Visibility.Visible;


                BtnConfirmar.IsEnabled =
                    true;
            }
            else
            {
                _metodoPago =
                    "Efectivo";


                PanelEfectivo.Visibility =
                    Visibility.Visible;


                PanelTarjeta.Visibility =
                    Visibility.Collapsed;


                ValidarEfectivo();
            }
        }


        // =========================================================
        // DINERO RECIBIDO
        // =========================================================

        private void Recibido_TextChanged(
            object sender,
            TextChangedEventArgs e)
        {
            ValidarEfectivo();
        }


        private void ValidarEfectivo()
        {
            if (TxtRecibido == null ||
                TxtCambio == null ||
                BtnConfirmar == null)
            {
                return;
            }


            if (_metodoPago !=
                "Efectivo")
            {
                return;
            }


            if (!IntentarLeerDecimal(
                    TxtRecibido.Text,
                    out decimal recibido))
            {
                TxtCambio.Text =
                    "Ingresa una cantidad válida";


                BtnConfirmar.IsEnabled =
                    false;


                return;
            }


            decimal cambio =
                recibido - _total;


            if (cambio < 0)
            {
                TxtCambio.Text =
                    $"Faltan {Math.Abs(cambio):C}";


                BtnConfirmar.IsEnabled =
                    false;


                return;
            }


            TxtCambio.Text =
                $"Cambio: {cambio:C}";


            BtnConfirmar.IsEnabled =
                true;
        }


        // =========================================================
        // CONVERTIR TEXTO A DECIMAL
        // =========================================================

        private static bool IntentarLeerDecimal(
            string? texto,
            out decimal valor)
        {
            valor = 0m;


            if (string.IsNullOrWhiteSpace(
                    texto))
            {
                return false;
            }


            texto =
                texto.Trim()
                .Replace("$", "")
                .Replace(" ", "");


            // -----------------------------------------------------
            // CULTURA ACTUAL
            // -----------------------------------------------------

            if (decimal.TryParse(
                    texto,
                    NumberStyles.Number,
                    CultureInfo.CurrentCulture,
                    out valor))
            {
                return true;
            }


            // -----------------------------------------------------
            // FORMATO CON PUNTO DECIMAL
            // -----------------------------------------------------

            if (decimal.TryParse(
                    texto,
                    NumberStyles.Number,
                    CultureInfo.InvariantCulture,
                    out valor))
            {
                return true;
            }


            return false;
        }
    }
}
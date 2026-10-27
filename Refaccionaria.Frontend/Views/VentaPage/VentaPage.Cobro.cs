using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;
using Microsoft.UI.Xaml.Media.Imaging;
 
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
 
using QRCoder;
 
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;
 
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
 
 
            CancelarSimulacion();
 
 
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
 
 
                // La venta se confirma sola cuando el
                // teléfono aprueba el pago.
                BtnConfirmar.IsEnabled =
                    false;
 
 
                _ = SimularPagoTarjetaAsync();
            }
            else
            {
                _metodoPago =
                    "Efectivo";
 
 
                CancelarSimulacion();
 
 
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
 
 
        // =========================================================
        // PAGO CON TARJETA SIMULADO (QR)
        // =========================================================
 
        private CancellationTokenSource? _simulacionPago;
 
 
        private enum VistaPago
        {
            Qr,
            Procesando,
            Aprobado
        }
 
 
        private void MostrarVistaPago(VistaPago vista)
        {
            if (CajaQr == null)
            {
                return;
            }
 
            CajaQr.Visibility =
                vista == VistaPago.Qr ? Visibility.Visible : Visibility.Collapsed;
 
            AnilloPago.Visibility =
                vista == VistaPago.Procesando ? Visibility.Visible : Visibility.Collapsed;
 
            AnilloPago.IsActive =
                vista == VistaPago.Procesando;
 
            PistonAprobado.Visibility =
                vista == VistaPago.Aprobado ? Visibility.Visible : Visibility.Collapsed;
 
            Storyboard animacion =
                (Storyboard)PanelTarjeta.Resources["AnimPistonAprobado"];
 
            if (vista == VistaPago.Aprobado)
            {
                animacion.Begin();
            }
            else
            {
                animacion.Stop();
            }
        }
 
 
        private async Task SimularPagoTarjetaAsync()
        {
            CancelarSimulacion();
 
            CancellationTokenSource cts = new();
            _simulacionPago = cts;
 
            string referencia =
                Random.Shared.Next(10000, 100000).ToString();
 
            string textoQr =
                $"Refaccionaria - Pago con tarjeta - Total: {_total:C} - Ref: {referencia}";
 
            ImgQr.Source =
                await CrearImagenQrAsync(textoQr);
 
            MostrarVistaPago(VistaPago.Qr);
 
            TxtEstadoPago.Text =
                "Esperando pago…";
 
            try
            {
                // 1. Tiempo para que escaneen el QR
                await Task.Delay(TimeSpan.FromSeconds(8), cts.Token);
 
                // 2. Procesando
                MostrarVistaPago(VistaPago.Procesando);
 
                TxtEstadoPago.Text =
                    "Procesando pago…";
 
                await Task.Delay(TimeSpan.FromSeconds(3), cts.Token);
 
                // 3. Aprobado: pistón con pulgar arriba
                string autorizacion =
                    Random.Shared.Next(100000, 1000000).ToString();
 
                MostrarVistaPago(VistaPago.Aprobado);
 
                TxtEstadoPago.Text =
                    $"¡Pago aprobado! · Autorización {autorizacion}";
 
                await Task.Delay(TimeSpan.FromSeconds(3), cts.Token);
            }
            catch (OperationCanceledException)
            {
                return; // se canceló el cobro o cambiaron a Efectivo
            }
 
            if (CapaCobro.Visibility != Visibility.Visible ||
                _metodoPago != "Tarjeta")
            {
                return;
            }
 
            // Registrar la venta con el flujo que ya tienen
            Confirmar_Click(this, new RoutedEventArgs());
        }
 
 
        private void CancelarSimulacion()
        {
            _simulacionPago?.Cancel();
            _simulacionPago = null;
 
            if (ImgQr != null)
            {
                ImgQr.Source = null;
            }
 
            MostrarVistaPago(VistaPago.Qr);
        }
 
 
        private static async Task<BitmapImage> CrearImagenQrAsync(
            string texto)
        {
            byte[] png =
                PngByteQRCodeHelper.GetQRCode(
                    texto,
                    QRCodeGenerator.ECCLevel.M,
                    10
                );
 
            BitmapImage imagen = new();
 
            using MemoryStream stream = new(png);
 
            await imagen.SetSourceAsync(
                stream.AsRandomAccessStream()
            );
 
            return imagen;
        }
    }
}
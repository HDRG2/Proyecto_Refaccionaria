using Microsoft.UI;
using Microsoft.UI.Xaml.Data;
using Microsoft.UI.Xaml.Media;
using System;
using Windows.UI;

namespace Refaccionaria.Frontend.Converters
{
    // Ajusta el namespace de arriba si tu carpeta Converters usa otro
    // (por ejemplo Refaccionaria.Frontend.Converters).
    public class StockBajoABrushConverter : IValueConverter
    {
        private static readonly SolidColorBrush Rojo = new(Color.FromArgb(255, 0xDC, 0x35, 0x45));
        private static readonly SolidColorBrush Verde = new(Color.FromArgb(255, 0x19, 0x87, 0x54));

        public object Convert(object value, Type targetType, object parameter, string language)
        {
            bool bajoStock = value is bool b && b;
            return bajoStock ? Rojo : Verde;
        }

        public object ConvertBack(object value, Type targetType, object parameter, string language)
        {
            throw new NotImplementedException();
        }
    }
}

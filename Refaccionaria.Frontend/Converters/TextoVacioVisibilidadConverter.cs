using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Data;
using System;

namespace Refaccionaria.Frontend.Converters
{
    public class TextoVacioAVisibilidadConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, string language)
        {
            string texto = value?.ToString() ?? string.Empty;

            return string.IsNullOrEmpty(texto)
                ? Visibility.Visible
                : Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, string language)
        {
            throw new NotImplementedException();
        }
    }
}
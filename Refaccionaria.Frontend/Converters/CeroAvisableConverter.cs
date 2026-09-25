using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Data;

namespace Refaccionaria.Frontend.Converters;

public class CeroAVisibleConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, string language)
    {
        var cantidad = value is int i ? i : 0;
        return cantidad == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    public object ConvertBack(object value, Type targetType, object parameter, string language)
        => throw new NotImplementedException();
}
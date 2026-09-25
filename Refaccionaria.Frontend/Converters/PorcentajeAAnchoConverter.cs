using Microsoft.UI.Xaml.Data;

namespace Refaccionaria.Frontend.Converters;

public class PorcentajeAAnchoConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, string language)
    {
        if (value is double porcentaje)
            return porcentaje * 200;
        return 0;
    }

    public object ConvertBack(object value, Type targetType, object parameter, string language)
        => throw new NotImplementedException();
}
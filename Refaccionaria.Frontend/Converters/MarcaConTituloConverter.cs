using Microsoft.UI.Xaml.Data;

namespace Refaccionaria.Frontend.Converters;

public class MarcaConTituloConverter : IValueConverter
{
    public object Convert(object value, Type targetType, object parameter, string language)
    {
        var marca = value as string;
        return string.IsNullOrWhiteSpace(marca) ? "Marca no especificada" : $"Marca: {marca}";
    }

    public object ConvertBack(object value, Type targetType, object parameter, string language)
        => throw new NotImplementedException();
}
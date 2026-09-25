using CommunityToolkit.Mvvm.ComponentModel;
using Refaccionaria.Backend.Repositories;

namespace Refaccionaria.Frontend.Models;

public partial class Categoria : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private string nombre = string.Empty;
}




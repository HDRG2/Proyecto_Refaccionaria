using System.Collections.Generic;
using System.Threading.Tasks;

namespace Refaccionaria.Backend.Repositories;

public interface IRepository<T> where T : class, IEntity
{
    string CarpetaData { get; }
    Task<IEnumerable<T>> GetAllAsync();
    Task<T?> GetByIdAsync(int id);
    Task AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(int id);
    Task ReloadAsync();

}

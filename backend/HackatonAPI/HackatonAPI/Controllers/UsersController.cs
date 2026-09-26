using Microsoft.AspNetCore.Mvc;
using HackatonAPI.Models;

namespace HackatonAPI.Controllers
{
    public class CreateOrUpdateUserRequest
    {
        public string City { get; set; }
        public List<string>? Categories { get; set; }
    }


    [ApiController]
    [Route("users")]
    public class UsersController : ControllerBase
    {
        [HttpGet("{maxId}")]
        public async Task<ActionResult<User>> GetUser(string maxId)
        {
            await using var ctx = new UsersContext();

            await ctx.Database.EnsureCreatedAsync();

            // parsing maxId to long type
            if (!long.TryParse(maxId, out long maxIdL))
            {
                return BadRequest("Given ID is incorrect");
            }

            var user = ctx.Users
                .Where(u => u.MaxId == maxIdL)
                .FirstOrDefault();

            if (user is null)
            {
                return NotFound("User with given id not found");
            }

            return Ok(user);
        }

        [HttpPost("{maxId}")]
        public async Task<ActionResult> AddOrUpdateUser(string maxId, CreateOrUpdateUserRequest request)
        {
            await using var ctx = new UsersContext();

            await ctx.Database.EnsureCreatedAsync();

            // parsing maxId to long type
            if (!long.TryParse(maxId, out long maxIdL))
            {
                return BadRequest("Given ID is incorrect");
            }

            try
            {
                // get user
                var user = ctx.Users
                    .Where(u => u.MaxId == maxIdL)
                    .FirstOrDefault();

                if (user is null)
                {
                    // create
                    ctx.Users.Add(new User
                    {
                        MaxId = maxIdL,
                        City = request.City,
                        Categories = request.Categories
                    });
                    await ctx.SaveChangesAsync();
                }
                else
                {
                    // update
                    user.City = request.City;
                    user.Categories = request.Categories;
                    await ctx.SaveChangesAsync();
                }

                return Ok();
            }
            catch (Exception ex)
            {
                return BadRequest(new ProblemDetails
                {
                    Status = StatusCodes.Status500InternalServerError,
                    Detail = ex.Message
                });
            }
        }
    }
}

using Microsoft.AspNetCore.Mvc;
using HackatonAPI.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Http.HttpResults;

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
        public async Task<ActionResult<User>> GetUser(long maxId)
        {
            await using var ctx = new UsersContext();

            await ctx.Database.EnsureCreatedAsync();

            var user = ctx.Users
                .Where(u => u.MaxId == maxId)
                .FirstOrDefault();

            if (user is null)
            {
                return NotFound("User with given id not found");
            }

            return Ok(user);
        }

        [HttpPost("{maxId}")]
        public async Task<ActionResult> AddOrUpdateUser(long maxId, CreateOrUpdateUserRequest request)
        {
            await using var ctx = new UsersContext();

            await ctx.Database.EnsureCreatedAsync();

            try
            {
                // get user
                var user = ctx.Users
                    .Where(u => u.MaxId == maxId)
                    .FirstOrDefault();

                if (user is null)
                {
                    // create
                    ctx.Users.Add(new User
                    {
                        MaxId = maxId,
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

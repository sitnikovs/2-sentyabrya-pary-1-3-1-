class travelBlog:
    total_blogs = 0

Tb1 = travelBlog()
Tb1.name = "Франция"
Tb1.days = 6
travelBlog.total_blogs += 1

Tb2 = travelBlog()
Tb2.name = "Италия"
Tb2.days = 5
travelBlog.total_blogs += 1 
print(travelBlog.total_blogs)
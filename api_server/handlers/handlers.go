package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"

	"../database"
	"../models"
	"github.com/die-net/lrucache"
)

var cache = lrucache.New(104857600*3, 60*60*24) //300 Mb, 24 hours
var postsPerPage = 100
var catsPerPage = 100

func PostsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	page := url.QueryEscape(strings.Split(r.RequestURI, "/")[2])
	p, err := strconv.Atoi(page)
	if err != nil {
		return
	}

	cached, isCached := cache.Get("posts_" + page)
	if isCached == false {
		db := database.Connect()
		defer db.Close()

		query := fmt.Sprintf(`SELECT 
			posts.content, 
			COALESCE(posts.image, ''), 
			cats.title, 
			cats.slug, 
			(SELECT 
				COUNT(*) 
				FROM tasks_post) 
			FROM tasks_post as posts 
			INNER JOIN tasks_category AS cats ON posts.category_id = cats.id 
			ORDER BY posts.id DESC 
			LIMIT %[1]d OFFSET %[2]d;`, postsPerPage, postsPerPage*p)

		rows, err := db.Query(query)
		if err != nil {
			return
		}
		defer rows.Close()

		posts := make([]models.Post, 0)
		for rows.Next() {
			post := models.Post{}
			err := rows.Scan(&post.Content, &post.Image, &post.CategoryID.Title,
				&post.CategoryID.Slug, &post.TotalPosts)
			if err != nil {
				return
			}
			posts = append(posts, post)
		}
		if err = rows.Err(); err != nil {
			return
		}

		j, err := json.Marshal(posts)
		if err != nil {
			return
		}

		cache.Set("posts_"+page, j)
		w.Write(j)
	}
	w.Write(cached)
}

func PostsByCatHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	cat := url.QueryEscape(strings.Split(r.RequestURI, "/")[2])
	if len(cat) == 0 {
		return
	}
	page := url.QueryEscape(strings.Split(r.RequestURI, "/")[3])
	p, err := strconv.Atoi(page)
	if err != nil {
		return
	}

	cached, isCached := cache.Get("posts_cat_" + cat + "_" + page)
	if isCached == false {
		db := database.Connect()
		defer db.Close()

		query := fmt.Sprintf(`SELECT 
			posts.content, 
			COALESCE(posts.image, ''), 
			cats.title, 
			cats.slug, 
			(SELECT 
				COUNT(*) 
				FROM tasks_post AS posts 
				INNER JOIN tasks_category AS cats ON posts.category_id = cats.id 
				WHERE cats.slug='%[1]s') 
			FROM tasks_post AS posts 
			INNER JOIN tasks_category AS cats ON posts.category_id = cats.id 
			WHERE cats.slug='%[1]s' 
			ORDER BY posts.id DESC 
			LIMIT %[2]d OFFSET %[3]d;`, cat, postsPerPage, postsPerPage*p)
		rows, err := db.Query(query)
		if err != nil {
			return
		}
		defer rows.Close()

		posts := make([]models.Post, 0)
		for rows.Next() {
			post := models.Post{}
			err := rows.Scan(&post.Content, &post.Image, &post.CategoryID.Title,
				&post.CategoryID.Slug, &post.TotalPosts)
			if err != nil {
				return
			}
			posts = append(posts, post)
		}
		if err = rows.Err(); err != nil {
			return
		}

		j, err := json.Marshal(posts)
		if err != nil {
			return
		}

		cache.Set("posts_cat_"+cat+"_"+page, j)
		w.Write(j)
	}
	w.Write(cached)
}

func CategoriesHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	page := url.QueryEscape(strings.Split(r.RequestURI, "/")[2])
	p, err := strconv.Atoi(page)
	if err != nil {
		return
	}

	cached, isCached := cache.Get("cats_" + page)
	if isCached == false {
		db := database.Connect()
		defer db.Close()

		query := fmt.Sprintf(`SELECT 
			cats.title, 
			cats.slug, 
			COUNT(posts.id) AS cnt, 
			(SELECT 
				COUNT(*) 
				FROM tasks_category) 
			FROM tasks_category AS cats 
			INNER JOIN tasks_post AS posts ON posts.category_id = cats.id 
			GROUP BY (cats.title, cats.slug) 
			ORDER BY cats.title 
			LIMIT %[1]d OFFSET %[2]d;`, catsPerPage, catsPerPage*p)

		rows, err := db.Query(query)
		if err != nil {
			return
		}
		defer rows.Close()

		categories := make([]models.Category, 0)
		for rows.Next() {
			category := models.Category{}

			err := rows.Scan(&category.Title, &category.Slug, &category.PostCnt, &category.TotalCats)
			if err != nil {
				return
			}

			categories = append(categories, category)
		}
		if err = rows.Err(); err != nil {
			return
		}

		j, err := json.Marshal(categories)
		if err != nil {
			return
		}

		cache.Set("cats_"+page, j)
		w.Write(j)
	}
	w.Write(cached)
}

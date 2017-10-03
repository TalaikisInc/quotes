package models

import (
	"encoding/json"
)

type Post struct {
	Content    string
	Image      string
	CategoryID Category
	TotalPosts int
}

type PostJSON struct {
	Content    string   `json:"content"`
	Image      string   `json:"image"`
	CategoryID Category `json:"category_id, omitempty"`
	TotalPosts int      `json:"total_posts"`
}

func (p *Post) MarshalJSON() ([]byte, error) {
	return json.Marshal(PostJSON{
		p.Content,
		p.Image,
		p.CategoryID,
		p.TotalPosts,
	})
}

func (p *Post) UnmarshalJSON(b []byte) error {
	temp := &PostJSON{}

	if err := json.Unmarshal(b, &temp); err != nil {
		return err
	}

	p.Content = temp.Content
	p.Image = temp.Image
	p.CategoryID = temp.CategoryID
	p.TotalPosts = temp.TotalPosts

	return nil
}

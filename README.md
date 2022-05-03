## Welcome to GitHub Pages

You can use the [editor on GitHub](https://github.com/KissPeter/fastapi-middlewares/edit/main/README.md) to maintain and preview the content for your website in Markdown files.

Whenever you commit to this repository, GitHub Pages will run [Jekyll](https://jekyllrb.com/) to rebuild the pages in your site, from the content in your Markdown files.

### Baseline measurement

| **Test attribute** | **Test run 1** | **Test run 2** | **Test run 3** | **Average** |
|---|---|---|---|---|
| Requests per second | 1022.9 | 1026.24 | 923 | **990,71** |
| Time per request [ms] | 97.762 | 97.443 | 108.260 | **97,6025** |


### With one middleware

| **Test attribute** | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
|---|---|---|---|---|---|
| Requests per second | 686,21 | 689,44 | 674,9 | **683,52** | -44,94 |
| Time per request [ms] | 145,728 | 145,044 | 148,17 | **146,31** | 33,29 |

### With two middlewares

| **Test attribute** | **Test run 1** | **Test run 2** | **Test run 3** | **Average** | Difference to baseline [%] |
|---|---|---|---|---|---|
| Requests per second | 481,74 | 495,27 | 485,43 | **487,48** | -103,23 |
| Time per request [ms] | 207,58 | 201,91 | 206,005 | **205,17** | 52,43 |

Markdown is a lightweight and easy-to-use syntax for styling your writing. It includes conventions for

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```

For more details see [Basic writing and formatting syntax](https://docs.github.com/en/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/KissPeter/fastapi-middlewares/settings/pages). The name of this theme is saved in the Jekyll `_config.yml` configuration file.

### Support or Contact

Having trouble with Pages? Check out our [documentation](https://docs.github.com/categories/github-pages-basics/) or [contact support](https://support.github.com/contact) and we’ll help you sort it out.

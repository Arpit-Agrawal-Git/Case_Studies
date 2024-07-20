library(shiny)
library(httr)
library(jsonlite)

ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      .container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        width: 100%;
      }
      .box {
        max-width: 600px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
      }
    "))
  ),
  div(class = "container",
      div(class = "box",
          titlePanel("Claim Cost Predictor"),
          div(
            textInput("accident_state", "Accident State", value = ""),
            textInput("industry_type", "Sector/Industry", value = ""),
            textInput("cause_description", "Cause Description", value = ""),
            dateInput("report_date", "Report Date", value = Sys.Date()),
            dateInput("loss_date", "Loss Date", value = Sys.Date()),
            textInput("loss_type", "Loss Type", value = ""),
            selectInput("litigation_status", "Litigation Status", choices = c("", "YES", "NO")),
            textInput("occupation", "Occupation", value = ""),
            actionButton("predict_btn", "Get Prediction"),
            div(id = "error", style = "color:red;")
          ),
          h3(textOutput("result"), style = "color:green;")
      )
  )
)

server <- function(input, output) {
  observeEvent(input$predict_btn, {
    output$error <- renderText("")
    output$result <- renderText("")
    
    # Validate inputs
    if (is.null(input$accident_state) || input$accident_state == "" ||
        is.null(input$industry_type) || input$industry_type == "" ||
        is.null(input$cause_description) || input$cause_description == "" ||
        is.null(input$report_date) || is.na(input$report_date) ||
        is.null(input$loss_date) || is.na(input$loss_date) ||
        is.null(input$loss_type) || input$loss_type == "" ||
        is.null(input$litigation_status) || input$litigation_status == "" ||
        is.null(input$occupation) || input$occupation == "") {
      output$error <- renderText("All fields are required.")
      return()
    }
    
    # Check if Loss Date is not after Report Date
    if (as.Date(input$loss_date) > as.Date(input$report_date)) {
      output$error <- renderText("Loss Date cannot be after Report Date.")
      return()
    }
    
    # Prepare data for prediction
    data <- list(
      `Accident State` = unlist(input$accident_state),
      `Sector/Industry` = unlist(input$industry_type),
      `Cause Description` = unlist(input$cause_description),
      `Report Date` = as.character(unlist(input$report_date)),
      `Loss Date` = as.character(unlist(input$loss_date)),
      `Loss Type` = unlist(input$loss_type),
      Litigation = unlist(input$litigation_status),
      Occupation = unlist(input$occupation)
    )
    
    # Send data to backend for prediction
    response <- POST("http://localhost:5000/process", 
                     body = toJSON(data, auto_unbox = TRUE), 
                     encode = "json",
                     content_type_json())
    
    if (response$status_code == 200) {
      result <- content(response)
      output$result <- renderText(paste("Predicted Claim Cost: $", result[[1]]$`Predicted Claim Cost`))
    } else {
      output$error <- renderText("An error occurred while predicting the claim cost.")
    }
  })
}

shinyApp(ui = ui, server = server)

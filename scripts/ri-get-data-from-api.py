
# get /key-stages
# returns: ["slug" "title"]

# get /key-stages/{keyStage}/subjects
# returns: ["subjectSlug" "subjectTitle"]

# get /key-stages/{keyStage}/subject/{subject}/units
# returns ["unitSlug" "unitTitle"]

# get /key-stages/{keyStage}/subject/{subject}/lessons
# ?unit ?offset ?limit
# returns [ "unitSlug" "unitTitle" "lessons":[ "lessonTitle" "lessonSlug"]]

# get /lessons/{lesson}/summary
# { "keyLearningPoints"}

#get /lessons/{lesson}/quiz
# list of questions
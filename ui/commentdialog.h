#pragma once

#include "binaryninjaapi.h"
#include "dialogtextedit.h"
#include "uicomment.h"
#include "uicontext.h"
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDialog>

class BINARYNINJAUIAPI CommentDialog : public QDialog
{
	Q_OBJECT

	DialogTextEdit* m_comment;
	UIComment m_uicomment;

 public:
	CommentDialog(QWidget* parent, const UIComment& comment);
	QString getNewComment();
	QString getCurrentComment();
	const FunctionRef& getCommentBackingFunction();
	const BinaryViewRef& getCommentBackingData();
	UICommentType getCommentType();
	uint64_t getCommentAddress();
};

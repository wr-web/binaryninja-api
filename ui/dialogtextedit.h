#pragma once

#include "uicontext.h"
#include <QtWidgets/QTextEdit>

class BINARYNINJAUIAPI DialogTextEdit : public QTextEdit
{
	Q_OBJECT

 public:
	DialogTextEdit(QWidget* parent);

 protected:
	virtual void keyPressEvent(QKeyEvent* event) override;

 Q_SIGNALS:
	void contentAccepted();
};

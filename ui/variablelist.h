#pragma once

#include <QtWidgets/QListWidget>
#include <QtWidgets/QWidget>

#include "dockhandler.h"
#include "viewframe.h"

class BINARYNINJAUIAPI VariableListView : public QWidget, public DockContextHandler {
    Q_OBJECT
    Q_INTERFACES(DockContextHandler)

    ViewFrame* m_view;
    BinaryViewRef m_data;

    QListWidget* m_list;

public:
    VariableListView(ViewFrame* view, BinaryViewRef data);

    void updateContent();
};
